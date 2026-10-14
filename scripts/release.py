"""Build and verify the unmanaged solution using only the Python standard library."""

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
from zipfile import ZIP_STORED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
if os.name == "nt" and not str(ROOT).startswith("\\\\?\\"):
    ROOT = Path("\\\\?\\" + str(ROOT))

NO_SECURE_INPUTS = {
    "AppendToArrayVariable", "AppendToStringVariable", "DecrementVariable",
    "Foreach", "If", "IncrementVariable", "InitializeVariable", "Recurrence",
    "Scope", "SetVariable", "Switch", "Terminate", "Until",
}
NO_SECURE_OUTPUTS = NO_SECURE_INPUTS | {"Compose", "ParseJson", "Response", "Wait"}
SECRET_FIELDS = {"clientsecret", "password", "accesstoken", "refreshtoken", "connectionstring"}
LIVE_CONNECTION_FIELDS = {"connectionid", "connectionresourceid"}
DESIGNER_UNKNOWN_FUNCTIONS = ("slice(", "uriHost(", "workflow()")


def validate_connection_values(value, location):
    if isinstance(value, dict):
        for key, item in value.items():
            field = re.sub(r"[_-]", "", key.lower())
            path = location + "." + key
            if isinstance(item, str) and item.strip():
                if field in SECRET_FIELDS:
                    raise ValueError(f"Do not package a secret credential value in {path}.")
                if field in LIVE_CONNECTION_FIELDS:
                    raise ValueError(f"Do not package a live connection binding in {path}.")
                if field == "connectionname" and (
                        re.fullmatch(r"[0-9a-fA-F-]{36}|[0-9a-fA-F]{32}", item)
                        or "/connections/" in item.lower()):
                    raise ValueError(f"Do not package a live connection name in {path}.")
            validate_connection_values(item, path)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            validate_connection_values(item, f"{location}[{index}]")


def source_files(root=ROOT):
    source = root / "source"
    return {file.relative_to(source).as_posix(): file.read_bytes()
            for file in sorted(source.rglob("*")) if file.is_file()}


def read_version(files):
    manifest = ET.fromstring(files["solution.xml"]).find("SolutionManifest")
    version = manifest.findtext("Version")
    if not re.fullmatch(r"\d+\.\d+\.\d+\.\d+", version or ""):
        raise ValueError("Solution version must contain four numeric components.")
    if manifest.findtext("Managed") != "0":
        raise ValueError("The customer package must be unmanaged.")
    return version


def validate_source(files):
    required = {"solution.xml", "customizations.xml", "[Content_Types].xml"}
    if not required <= files.keys():
        raise ValueError("Missing required solution files.")
    for name, content in files.items():
        if re.search(rb"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----", content):
            raise ValueError(f"Do not package private credential material in {name}.")
        if name.endswith(".xml"):
            document = ET.fromstring(content)
            for node in document.iter():
                field = node.tag.split("}")[-1].lower()
                if field in SECRET_FIELDS | LIVE_CONNECTION_FIELDS and (node.text or "").strip():
                    raise ValueError(f"Do not package credential values or live connection bindings in {name}:{field}.")
        elif name.endswith(".json"):
            validate_connection_values(json.loads(content), name)
        elif name.endswith("/data") and re.search(
                rb"(?im)^\s*(connectionId|connectionResourceId|connectionString|clientSecret|accessToken|refreshToken|password|authorization)\s*:\s*\S",
                content):
            raise ValueError(f"Review credential or live connection settings in {name}; package unbound references only.")
    version = read_version(files)
    custom = ET.fromstring(files["customizations.xml"])
    expected = {"cat_agentcatalogue", "cat_agentintakerequest", "cat_tenantagentinventory"}
    actual = {entity.findtext("Name", "").lower() for entity in custom.findall("./Entities/Entity")}
    if actual != expected:
        raise ValueError("The package must contain exactly the three documented business tables.")
    bots = [ET.fromstring(content) for name, content in files.items()
            if name.startswith("bots/") and name.endswith("/bot.xml")]
    if (len(bots) != 1 or bots[0].get("schemaname") != "cre2b_agentcoefrontdoor"
            or bots[0].findtext("name") != "Agent CoE Front Door"):
        raise ValueError("Package only the actual Agent CoE Front Door agent, not test agents.")
    if bots[0].findtext("accesscontrolpolicy") != "1":
        raise ValueError("The instruction-enabled agent must use explicit agent-reader access.")
    configuration = json.loads(files["bots/cre2b_agentcoefrontdoor/configuration.json"])
    segments = configuration["agentSettings"]["instructions"]["segments"]
    if (len(segments) != 1 or segments[0].get("$kind") != "StaticSegment"
            or not isinstance(segments[0].get("value"), str) or not segments[0]["value"].strip()):
        raise ValueError("Package parent instructions as one nonempty designer-compatible static segment.")
    if len(custom.findall("./Workflows/Workflow")) != 2:
        raise ValueError("Keep only the required inventory and decision-notification flows.")
    references = {ref.get("connectionreferencelogicalname")
                  for ref in custom.findall("./connectionreferences/connectionreference")}
    if any(name.lower().endswith((".dll", ".nupkg")) for name in files):
        raise ValueError("This low-code package must not include a parser plugin or assembly.")
    for workflow in custom.findall("./Workflows/Workflow"):
        if (workflow.findtext("StateCode"), workflow.findtext("StatusCode")) != ("0", "1"):
            raise ValueError("All packaged flows must be Off.")
        if workflow.findtext("ModernFlowType") != "1":
            raise ValueError("Package both flows as Copilot Studio agent flows.")
        name = workflow.findtext("JsonFileName", "").lstrip("/")
        if name not in files:
            raise ValueError(f"Missing workflow definition: {name}")
        properties = json.loads(files[name])["properties"]
        for reference in properties.get("connectionReferences", {}).values():
            connection = reference.get("connection", {})
            if (set(connection) != {"connectionReferenceLogicalName"}
                    or connection["connectionReferenceLogicalName"] not in references):
                raise ValueError("Flow connections must contain only declared, unbound logical references.")
        validate_flow(properties["definition"])
        validate_designer(properties["definition"])
    for name, content in files.items():
        if name.startswith("botcomponents/") and name.endswith("/data"):
            text = content.decode("utf-8-sig")
            if text.startswith("kind: InlineAgentSkill"):
                lines = text.splitlines()
                if lines[-1] != "authoringSource: Blank":
                    raise ValueError("Inline skill authoringSource must be the final root property.")
                if any(line and not line.startswith("  ")
                       for line in lines[2:-1]):
                    raise ValueError("Inline skill instructions must remain inside content.")
        if name.endswith("environmentvariablevalue.xml"):
            raise ValueError("Target environment-variable values must not be packaged.")
        if name.endswith("_connectionparameters.json"):
            oauth = json.loads(content)["token"]["oAuthSettings"]
            if oauth.get("clientId") != "00000000-0000-0000-0000-000000000000":
                raise ValueError("Do not package a target OAuth client ID.")
            if oauth.get("clientSecret"):
                raise ValueError("Do not package a connector secret.")
    return version


def walk_actions(actions):
    for name, action in actions.items():
        yield name, action
        yield from walk_actions(action.get("actions", {}))
        yield from walk_actions(action.get("else", {}).get("actions", {}))


def validate_designer(definition):
    graphs = [trigger.get("metadata", {}).get("associatedData", {}).get("graph")
              for trigger in definition.get("triggers", {}).values()]
    graph = graphs[0] if len(graphs) == 1 else None
    if not isinstance(graph, dict) or not graph.get("nodes") or not isinstance(graph.get("edges"), list):
        raise ValueError("Each flow must include exactly one saved Workflows designer graph.")
    node_ids = [node.get("id") for node in graph["nodes"]]
    if len(node_ids) != len(set(node_ids)):
        raise ValueError("The designer graph must not contain duplicate node IDs.")
    unknown = [name for name in DESIGNER_UNKNOWN_FUNCTIONS if name in json.dumps(definition["actions"])]
    if unknown:
        raise ValueError(f"Remove expressions the Workflows designer rejects: {unknown}")


def validate_flow(definition):
    names = [name for name, _ in walk_actions(definition["actions"])]
    if len(names) != len(set(names)):
        raise ValueError("Flow action names must be globally unique.")

    def check_scope(actions, depth=0):
        for name, action in actions.items():
            if depth > 8:
                raise ValueError(f"{name} exceeds Power Automate's eight-level nesting limit.")
            secured = action.get("runtimeConfiguration", {}).get("secureData", {}).get("properties", [])
            if action["type"] in NO_SECURE_INPUTS and "inputs" in secured:
                raise ValueError(f"{name}: {action['type']} does not support secure inputs.")
            if action["type"] in NO_SECURE_OUTPUTS and "outputs" in secured:
                raise ValueError(f"{name}: {action['type']} does not support explicit secure outputs.")
            if action["type"] == "ParseJson":
                pending = [action["inputs"]["schema"]]
                while pending:
                    schema = pending.pop()
                    if not isinstance(schema, dict):
                        continue
                    if {"pattern", "patternProperties"} & schema.keys():
                        raise ValueError(f"{name}: Parse JSON patterns are unsupported with OpenAPI connections.")
                    pending.extend(schema.get("properties", {}).values())
                    pending.extend(schema.get("definitions", {}).values())
                    pending.extend([schema.get("items"), schema.get("additionalProperties")])
                    for keyword in ["allOf", "anyOf", "oneOf"]:
                        pending.extend(schema.get(keyword, []))
            unknown = set(action.get("runAfter", {})) - actions.keys()
            if unknown:
                raise ValueError(f"{name} depends on an action outside its scope: {unknown}")
            check_scope(action.get("actions", {}), depth + 1)
            check_scope(action.get("else", {}).get("actions", {}), depth + 1)

    check_scope(definition["actions"])


def archive_bytes(files):
    output = io.BytesIO()
    with ZipFile(output, "w", compression=ZIP_STORED) as archive:
        for name, content in sorted(files.items()):
            item = ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            item.compress_type = ZIP_STORED
            item.create_system = 0
            item.external_attr = 0x20
            archive.writestr(item, content)
    return output.getvalue()


def package_name(version):
    return "AgentCoEFrontDoor_" + version.replace(".", "_") + ".zip"


def build(root=ROOT):
    files = source_files(root)
    version = validate_source(files)
    release = root / "release"
    release.mkdir(exist_ok=True)
    unexpected = {file.name for file in release.glob("*.zip")} - {package_name(version)}
    if unexpected:
        raise ValueError(f"Remove superseded candidate packages explicitly: {sorted(unexpected)}")
    content = archive_bytes(files)
    name = package_name(version)
    digest = hashlib.sha256(content).hexdigest().upper()
    (release / name).write_bytes(content)
    (release / "SHA256SUMS").write_text(f"{digest}  {name}\n", encoding="ascii")
    manifest = {
        "solution": "AgentCoEFrontDoor", "solutionVersion": version,
        "releaseTag": "v" + ".".join(version.split(".")[:3]),
        "package": name, "sha256": digest, "managed": False,
    }
    (release / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return verify(root)


def verify(root=ROOT):
    files = source_files(root)
    version = validate_source(files)
    release = root / "release"
    manifest = json.loads((release / "manifest.json").read_text(encoding="utf-8"))
    if manifest["solutionVersion"] != version or manifest["package"] != package_name(version):
        raise ValueError("Release manifest version or filename is inconsistent.")
    package = release / manifest["package"]
    content = package.read_bytes()
    digest = hashlib.sha256(content).hexdigest().upper()
    if digest != manifest["sha256"]:
        raise ValueError("Release checksum does not match the manifest.")
    if (release / "SHA256SUMS").read_text(encoding="ascii") != f"{digest}  {package.name}\n":
        raise ValueError("SHA256SUMS does not match the manifest.")
    with ZipFile(package) as archive:
        if archive.testzip() is not None:
            raise ValueError("Release ZIP CRC validation failed.")
        if len(archive.namelist()) != len(set(archive.namelist())):
            raise ValueError("Release ZIP contains duplicate paths.")
        if set(archive.namelist()) != files.keys():
            raise ValueError("Release ZIP paths differ from source.")
        if any(archive.read(name) != value for name, value in files.items()):
            raise ValueError("Release ZIP bytes differ from source.")
    if content != archive_bytes(files):
        raise ValueError("Release ZIP is not reproducible from the current source.")
    if len(list(release.glob("*.zip"))) != 1:
        raise ValueError("Keep only the single current solution ZIP in release.")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["build", "verify"])
    args = parser.parse_args()
    try:
        manifest = build() if args.command == "build" else verify()
    except (ValueError, KeyError, OSError, ET.ParseError) as error:
        print(f"Release {args.command} failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(manifest, indent=2))
    print("Local package checks only; this is not proof of live acceptance.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
