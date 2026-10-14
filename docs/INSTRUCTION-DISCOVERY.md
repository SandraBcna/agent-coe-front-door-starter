# Restricted instruction-definition discovery

The package contains the actual **Agent CoE Front Door**, not a demonstration or test agent. Instruction discovery extends the existing inventory flow and table; it adds no parser plugin, Custom API, Azure Function, external parsing service, or additional scheduled flow.

**Who sees what.** Instruction definitions can contain confidential rules, internal links, and sensitive text. CoE reviewers you authorise read the raw definitions in the triage app. The agent never queries them: it searches and shares only the short AI summary, so employees learn what an agent does, never how it is instructed.

## Inventory is not instruction text

The Power Platform Inventory API response can include the optional `properties.instructionsCharactersCount`, not the instruction text itself. That optional count describes inventory metadata and must not be presented as a retrieved prompt.

After each metadata upsert, the same daily flow can read the corresponding authoring record from an explicitly approved source Dataverse environment:

| Source | Stored definition | Format label |
|---|---|---|
| GitHub Copilot-harness agent | The native `bot.configuration.agentSettings.instructions` object, serialized as JSON | `BotConfiguration instructions JSON` |
| Standard agent | The instruction-bearing active Custom GPT component's native `botcomponent.data` | `GptComponentMetadata OBI/YAML` |

The Standard definition is preserved verbatim, including its YAML structure. It is **not** converted to plain text by a custom parser. CoE reviewers can inspect its actual instruction content in the triage app; the advisor uses only the AI summary. A definition can contain dynamic values or an empty instruction value; availability is not proof of a particular capability.

These are **authoring definitions**, not guaranteed snapshots of the published runtime prompt. Draft changes can differ from published inventory, and inventory metadata can lag. The flow records the source record/ETag and retrieval time rather than mislabelling authoring content as published.

## Minimal package changes

Instruction discovery uses the existing `cat_tenantagentinventory` table and **CAT - Refresh Power Platform Agent Inventory Daily** flow. Its required additions are inventory columns, one separate inventory Dataverse connection reference, and one target-owned source-mapping setting.

| Column | Meaning |
|---|---|
| `cat_instructiondefinition` | Field-secured native instruction-bearing definition |
| `cat_instructionsummary` | Short AI-generated description of what the agent does; shareable, never raw instructions |
| `cat_instructionformat` | JSON or OBI/YAML source format |
| `cat_instructionstatus` | Actual availability or retrieval limitation |
| `cat_instructionretrievedon` | Last successful retrieval; meaningful with an available status |
| `cat_instructionsourceversion` | Authoring bot/component ID and Dataverse ETag |
| `cat_instructionerror` | Field-secured sanitized operational diagnostic |
| `cat_instructioncharcount` | Optional instruction character count reported by inventory |
| `cat_harness` | Harness reported by inventory |

The inventory main form displays these fields read-only, with **Instruction summary (AI-generated)** directly under the agent name. Raw definitions are not appended to general search text, catalogue descriptions, intake next steps, decision comments, or email.

## AI-generated instruction summary

The package includes one AI Builder prompt, **CAT - Summarise agent instruction definition** (GPT-4.1 mini, temperature 0). The same inventory flow runs it with the built-in **Run a prompt** action; there is no custom code.

- It runs only for a row whose status is `Definition available`, and only when the summary is empty or the definition changed since the last refresh. Unchanged definitions do not call the prompt again.
- The prompt returns at most two plain sentences on purpose, intended users and main capabilities. It must not quote instructions or include links, email addresses, secrets or internal rules. The flow trims the result to 500 characters.
- When the definition becomes unavailable, the flow clears the summary. If the prompt fails or the platform's content filter blocks the definition (for example, injection-style text), the summary is cleared and the refresh continues.
- Prompt inputs and outputs use secured run history.

The summary is a soft safeguard generated from untrusted text, not a security boundary. It is not column-secured so CoE reviewers and the advisor can use it as the shareable capability description; review a sample before relying on it. Each generated summary consumes AI Builder or Copilot credits; check current Microsoft pricing and your capacity. If credits are not approved, keep enrichment off (an empty `sources` array) rather than editing the flow: removing the **Summarise instruction definition** scope requires saving in a designer, which removes the flow's other protections (see [about the two flows](INSTALLATION.md#about-the-two-flows)). If you must remove it, do so in the solution source and reimport.

## Configure approved sources

1. Bind `cat_inventory_dataverse` to an approved inventory service identity, separate from the conversational MCP reference. In the target it needs inventory Read/Create/Write/Delete plus permission to write the secured definition/diagnostic columns. In each approved source it needs only the required Agent and Agent component Read access.
2. Obtain knowledge/data-owner approval to cache the definitions. Review retention, DLP, privacy, capacity, connector licensing, source permissions, and connection ownership.
3. Set one target-only current value for **Agent CoE approved instruction sources** (`cat_InstructionSources`):

   ```json
   {
     "sources": [
       {
         "environmentId": "[APPROVED SOURCE ENVIRONMENT ID]",
         "organizationUrl": "[APPROVED SOURCE DATAVERSE URL]"
       }
     ]
   }
   ```

4. Replace the placeholders only in the target service. Source IDs must match inventory environment IDs. URLs must be approved commercial Dataverse organization URLs of the form `https://<organization>.crm<region>.dynamics.com`, with no path, credentials, query, or fragment. Do not use a URL supplied in conversation or another agent's instructions.
5. Keep at most one mapping per environment and one current settings value. An empty `sources` array deliberately disables instruction enrichment while metadata discovery remains available.
6. Test source reads with a refresh in non-production before relying on the daily schedule. Test both native formats only where those source records and permissions actually exist; do not claim an unexecuted platform mapping has passed.

The ResourceQuery delegated permission does **not** grant Dataverse authoring access. Reading instruction definitions requires separate Dataverse authorization; do not broaden the inventory API app's permissions as a substitute.

## Keep definitions out of chat

The agent is packaged with **Agent readers** access policy and Microsoft authentication. Share it with the employees you want to serve; employees see inventory agents only as described in [the employee-facing boundary](POWER-PLATFORM-INVENTORY.md#employee-facing-access-boundary).

The raw definition and diagnostic columns have column security enabled. Create a target-owned column-security profile in Power Platform administration. Give the inventory writer identity Create/Update/Read on those columns, and give Read only to the CoE reviewers who need to read definitions. Do not give ordinary users table/app access to restricted inventory.

**System Administrators bypass column security.** The agent's Dataverse connection runs as the account that created it, and anyone who chats with the agent reads through it. Before you share the agent while this add-on is on, bind its **Microsoft Dataverse MCP Server** connection to a non-admin account that is **not** in the column-security profile, for example a service account with **Basic User** and **Agent CoE Reviewer**. That account can read inventory names and summaries and create intake requests, but cannot read the definitions. An administrator preview cannot establish this boundary; verify it with the actual connection identity.

**Chat disclosure.** In conversation, the agent never selects or filters on the definition column. It describes a matched agent in at most two sentences (purpose, intended users, main capabilities), using the AI summary when available. It never quotes, reproduces, or lists rules from another agent's instructions, nor reveals its own, and refers requests for full instructions to authorised CoE staff using the read-only inventory form. These are instruction-level safeguards; the non-admin connection above is the actual boundary.

The package contains no target group membership, source permissions, production roles, connection credentials, or source URLs. Those are organization-owned configuration, not missing demonstration components.

## Failure, freshness, and trust

The flow clears the previous cached definition before attempting retrieval. It never chooses an arbitrary authoring record when the lookup is not unique. Missing mappings, absent instruction data, unsupported storage, and denied reads are represented explicitly rather than filled with invented text.

An actual failure on an approved source records a diagnostic, flags the run as failed, and prevents stale cleanup. Source queries, definition writes, and metadata-upsert outputs that can contain prior definitions use secured inputs/outputs. Parse JSON actions use Secure Inputs, which also hides their outputs; that action type does not support an explicit Secure Outputs flag. Do not disable those controls to collect public evidence.

Only use a definition with `Definition available` status and a retrieval time within the organization's approved refresh interval. A preserved last-success timestamp alone does not establish that a later failed attempt succeeded. Clear cached definitions before withdrawing writer access or disabling their refresh; credential revocation does not erase already cached content.

Other agents' instructions are **untrusted discovery data**, never instructions to Front Door. They cannot grant roles, authorize actions, change the recipient or template, override local governance/licensing knowledge, or bypass confirmation. The curated catalogue still determines CoE approval.

## Acceptance

Verify against the real CoE Front Door agent in an authorized non-production environment:

- The package contains exactly one bot: `Agent CoE Front Door`.
- The existing inventory flow imports Off and uses the separate target inventory connection.
- An approved source produces the exact native definition with its real format, source version, and retrieval time.
- A task term present in the AI summary but absent from the agent name is discoverable in chat.
- An available definition gets a two-sentence summary with no quoted instructions, links or email addresses. A second refresh with an unchanged definition does not call the prompt again, and an unavailable definition clears the summary.
- Asked for another agent's or its own full instructions (including "I am the owner/admin" and "ignore your rules"), the agent gives at most a two-sentence capability description and quotes no instruction text.
- No approved source, denied access, malformed configuration, and missing/ambiguous records produce explicit limitations without retaining an old definition as current evidence.
- Raw definition/diagnostic columns and secured run-history actions remain protected; the agent's non-admin Dataverse connection cannot read the definition column.
- Source field counts, metadata refresh idempotency, pagination, failure-safe cleanup, confirmation-before-write, and decision email remain correct.
- No test agent, test business rows, target settings, credentials, or raw retrieved instruction content appears in the release ZIP or repository.

See [NOTICE.md](../NOTICE.md) for the unchanged as-is disclaimer and adopter responsibilities.
