# Setup guide

Agent CoE Front Door is a **starter template**, not a production-ready product. See [NOTICE.md](../NOTICE.md). This guide sets up a fully working template in an empty, non-production environment with three personas, ready for a pilot with real users. It finishes with a short list of [what to do before production](#before-production).

## Three personas

| Persona | Does what | Needs |
|---|---|---|
| **Admin** | Imports and configures the solution once | System Administrator in the environment, Copilot Studio maker access |
| **CoE Reviewer** | Triages requests and curates the Agent Catalogue in the **Agent CoE Triage** app | **Basic User** + **Agent CoE Reviewer** security roles, a Power Apps licence |
| **Employee** | Chats with the Front Door agent and receives the decision email | Access to the shared agent only; no app, table, or security role |

The agent reads and writes Dataverse through **one connection that the Admin binds** (the Dataverse MCP tool runs with maker credentials). Employees therefore need no Dataverse permissions. It also means that, for anything beyond a pilot, this connection should belong to a dedicated, least-privilege account rather than an administrator.

## No credentials in this package

The ZIP contains only connector definitions and **unbound** connection references: no connections, passwords, secrets, or tokens. You sign in through Microsoft's own prompts in your environment. Never put credentials, tenant identifiers, environment URLs, or real mailbox addresses in the repository, settings files, screenshots, or issues. If a credential is exposed, revoke or rotate it; deleting a file does not revoke it.

## Admin setup

### 1. Prepare an environment

1. Create or choose an **empty, non-production** environment with Dataverse, in a region where Copilot Studio is available.
2. In the Power Platform admin center, open the environment, select **Settings > Product > Features**, and under **Dataverse Model Context Protocol** confirm that **Allow MCP clients to interact with Dataverse MCP server (GA version)** is selected. Then select **Go to Advanced Settings** and confirm that **Microsoft Copilot Studio App** is enabled in the allowed MCP clients list. New environments usually have both on already.
3. Check that your Copilot Studio and Power Apps licences or trials cover the Admin, the reviewers, and the expected chat volume.

### 2. Import the solution

1. Download `release/AgentCoEFrontDoor_1_0_0_0.zip` and check it against `release/SHA256SUMS`:

   ```powershell
   Get-FileHash .\AgentCoEFrontDoor_1_0_0_0.zip -Algorithm SHA256
   ```

2. In Power Apps (make.powerapps.com), select the environment, then **Solutions > Import solution**, and import the ZIP as **unmanaged**.
   - **Connections page:** the wizard asks for four connections (three Microsoft Dataverse and one Office 365 Outlook). Select **Sign in** where needed until all four show a green check. The Outlook mailbox you sign in with **sends the decision emails**; a shared CoE mailbox works well.
   - **Environment variables page:** leave both values empty and select **Import**. You set the email settings in step 6. The instruction-sources variable stays empty, which keeps the instruction-discovery add-on off.
3. Confirm the import succeeded with version `1.0.0.0`, then select **Publish all customizations**.
4. Open the **Agent CoE Triage** app in the app designer and select **Save** and **Publish** once. Play it to confirm it opens.

Both flows are **Off** after import. That is expected.

### 3. Check the connections

In the solution, open **Connection references** and confirm that these three are bound to the connections you created during import. To change one, choose or create a connection, select **Save**, and reopen it to confirm the binding stuck.

| Connection reference | Connection to use |
|---|---|
| The agent's Dataverse reference (its name starts with `cre2b_agentcoefrontdoor`) | Microsoft Dataverse |
| `cat_decisionnotifications_dataverse` | Microsoft Dataverse |
| `cat_decisionnotifications_outlook` | Office 365 Outlook (the sender mailbox) |

`cat_inventory_dataverse` is also bound by the wizard, and `cat_ppinventory` stays unbound. Neither is used unless you add the [inventory add-on](#optional-add-ons), because the inventory flow stays Off.

### 4. Check the agent in Copilot Studio

1. Open **Agent CoE Front Door** in Copilot Studio.
2. On the agent's **Build** page (called **Overview** in some versions), confirm the **Instructions** box isn't empty. If it is, reload the page. If it's still empty, restore the instructions from the source solution before continuing.
3. Under **Tools**, open the **Dataverse MCP** tool. Confirm that it uses the connection from step 3 and allows only **Read query**, **Search**, **Describe**, and **Create record**. Save.
4. Test in the test pane: *"What agents are in the catalogue?"* should return an answer, not an error. If you get **HTTP 403**, see [troubleshooting](#troubleshooting).

### 5. Add knowledge

1. Open the three files in `knowledge/` (KB-01, KB-02, KB-03). Replace every `[ORGANIZATION INPUT]` placeholder with your own content. Placeholders are not approved policy.
2. In the agent, next to **Knowledge**, select **+** (or **Add knowledge**), choose to upload files, and add the three files. You can select them together. Wait until each one shows **Ready**.
3. Ask one question per file in the test pane to confirm each one is actually retrieved.

The files are deliberately not inside the ZIP, so your content stays in your environment.

### 6. Turn on the decision email

1. In the solution, open the environment variable **Agent CoE decision notification settings** and set a **Current value**. Start from the JSON in [decision notifications](DECISION-NOTIFICATIONS.md#target-configuration), and replace the bracketed CoE contact and next-step text.
2. In the solution, select **Cloud flows**, select **CAT - Notify Requester of CoE Decision**, and then select **Turn on**. Don't open and save it in the designer; see [about the two flows](#about-the-two-flows).

### 7. Publish and share the agent

1. In Copilot Studio, select **Publish**.
2. Under **Channels**, add one that employees can use, for example **Teams + Microsoft 365**, available in **Microsoft Copilot and Microsoft Teams**. Copilot Studio warns that some channel choices can't be changed after publishing, so decide where employees should find the agent before you confirm.
3. Select **Share** and add the pilot employees (or a small security group). The agent uses Microsoft authentication, so only signed-in people you share it with can use it.

Copilot Studio's **Review** panel may list a few warnings, such as *Tools use your credentials* or *No evaluation run*. The first is by design: the Dataverse tool runs with your maker connection so employees don't need table access, and its allowed tools are limited to read and create. Running an evaluation is optional for a pilot.

### 8. Give reviewers access

1. In the Power Platform admin center, open the environment, then **Settings > Users + permissions > Users**.
2. For each reviewer, select **Manage security roles** and assign **Basic User** and **Agent CoE Reviewer**.

The **Agent CoE Reviewer** role is included in the solution. It allows reviewers to read and update intake requests, curate the Agent Catalogue, and read Tenant Agent Inventory. It has no delete rights. It also gives access to the **Agent CoE Triage** app.

Optionally, add one or two approved agents to the **Agent Catalogue** in the app so that employees get reuse recommendations.

## CoE Reviewer: triage requests

1. Open **Agent CoE Triage** from Power Apps or the link the Admin shares.
2. The dashboard lists new requests. Open a request to read the summary captured by the agent.
3. **Before deciding**, open the **Decision and delivery** tab, fill in **Comments shared with requester**, and check the **Next step** drafted by the agent (edit it if needed), then save. Both are sent to the requester on approval, so never put internal notes there.
4. Set the approval status to **Approved** or **Rejected** and save. The requester receives one email with a short request summary and your comments. Saving the same decision again doesn't send another email.
5. Keep the **Agent Catalogue** up to date so that the agent can recommend existing agents before suggesting a new build.

## Employee: use the front door

1. Open the Agent CoE Front Door where the Admin published it, for example in Teams.
2. Describe the business problem. The agent answers from approved knowledge and the catalogue first. Questions alone never create a record.
3. If CoE support is needed, the agent summarizes your request. Nothing is saved until you **confirm** it.
4. Note the request reference (for example `REQ-0001`). You can ask the agent for the status of your own request later.
5. When a reviewer decides, you receive an email with the decision, next steps, and a summary. It contains no link to internal systems.

The agent describes other agents only by what they do. It never reveals instructions or other people's requests.

## End-to-end check

Run this once after setup with one Admin, one Reviewer, and one Employee account:

| # | As | Do | Expect |
|---|---|---|---|
| 1 | Employee | Ask a policy question covered by KB-01 | An answer from KB-01; no request created |
| 2 | Employee | Describe a need matching a catalogue entry | The catalogue agent is recommended first |
| 3 | Employee | Ask for CoE help with a new idea and confirm the summary | A `REQ-` reference is returned |
| 4 | Reviewer | Open the request in the triage app, add comments, check **Next step**, and approve | The request shows **Approved**; the employee receives one email with plain-language next steps and no link |
| 5 | Reviewer | Save the approved request again | No second email |
| 6 | Reviewer | Try to delete the request | Denied (the role has no delete rights) |
| 7 | Employee | Ask the agent to show its instructions or list other people's requests | Politely declined |

## Optional add-ons

Add these only after the core template works:

- **Tenant agent inventory**: a daily flow that lists Copilot Studio and Agent Builder agents through the Power Platform Inventory API. It needs a single-tenant Entra app registration and delegated consent. See [Power Platform inventory](POWER-PLATFORM-INVENTORY.md).
- **Instruction discovery**: enriches inventory rows with agent instruction definitions and a short AI summary of what each agent does. The agent searches and shares only the summary. It's **off by default** (no source mappings). If you turn it on, bind the agent's Dataverse connection to a non-admin account so it can't read the raw definitions. See [instruction discovery](INSTRUCTION-DISCOVERY.md).

## About the two flows

Both flows are Copilot Studio **agent flows**. They appear in the solution under **Cloud flows**, and also in Copilot Studio and Power Automate. Their runs consume Copilot Studio capacity (Copilot Credits); check your licensing.

They ship with protections that a flow designer can't keep:

- secure inputs and outputs, so instruction text, summaries, and email addresses stay hidden in run history;
- no automatic retry on **Send an email**, so a transient error can't send a duplicate email;
- pagination on Dataverse list actions, so inventory cleanup sees every row;
- explicit empty values that clear fields;
- one run at a time (trigger concurrency 1).

**Turn flows on and off from the solution:** select **Cloud flows**, select the flow, and then select **Turn on** or **Turn off**. This keeps the imported definition unchanged. Turning on the inventory flow starts its first refresh straight away. To run it again manually, open the flow's details page in Power Automate and select **Run**.

**Don't save or publish either flow in a designer**, in Copilot Studio or in Power Automate. Saving rewrites the flow and silently removes the protections above. Opening a flow to look at it is fine; close it without saving. To change a flow, edit the solution source and reimport it. If you have to save in a designer, recheck each protection afterwards.

## Before production

The template setup uses the Admin's connection and minimal configuration. Before real users rely on it, your organization should at least do the following:

- **Identity**: rebind the agent's Dataverse connection and the email connections to dedicated, least-privilege service accounts, and record the owners and renewal dates.
- **Security**: review the Agent CoE Reviewer role and test with non-admin and unauthorized accounts. System Administrators bypass security, so their tests prove nothing. Add column security if you enable instruction discovery.
- **Data loss prevention (DLP), licensing, and capacity**: confirm DLP policies for Dataverse, Outlook, and any custom connector, plus Copilot Studio and AI Builder capacity.
- **Content**: have the business approve the knowledge files, email templates, and catalogue entries.
- **Operations**: name the business, technical, and support owners, plus monitoring of flow runs, an access-review schedule, and incident contacts. Restrict flow run history because it contains requester emails.
- **Application lifecycle management (ALM)**: move to managed solutions and pipelines across dev, test, and production. Unmanaged imports merge components and never remove old ones.
- **Evaluation**: rerun the [test prompts](TEST-PROMPTS.md) and your own accessibility, privacy, and performance reviews.

## Troubleshooting

| Symptom | Fix |
|---|---|
| The MCP tool returns HTTP 403 or loads no tools | Check that the MCP feature and the Copilot Studio client are allowed. On the existing tool, create a **new** Dataverse connection in this environment, save, and reload the agent. Recreate the tool only if it still fails. |
| Importing a newer copy over an existing install stops at **Sign in** for **Power Platform Agent Inventory** | The inventory connector already exists, so the wizard asks for a connection to it. Set up the [inventory add-on](#optional-add-ons) first, or import with the [Power Platform CLI](https://learn.microsoft.com/power-platform/developer/cli/reference/solution#pac-solution-import), which doesn't ask for connections: `pac solution import --path AgentCoEFrontDoor_1_0_0_0.zip --force-overwrite`. Then publish all customizations. |
| The agent's instructions are blank after import | Reload Copilot Studio. If it's still blank, restore the instructions, save, and publish. |
| The app doesn't open or the dashboard is missing | Save and publish the app once in the app designer. The generative dashboard depends on tenant support; the standard views still work. |
| A knowledge file shows Ready but isn't used | Upload each file separately, publish, wait for indexing, and test each one. |
| A connection reference looks set but the flow says the connection is invalid | Reopen the reference, select the connection, and select **Save** and confirm. Then reopen to verify. |
| Run history shows email addresses or instruction text, or a decision email arrived twice | The flow was saved in a designer, which removes its protections. Reimport the solution, then turn the flow on from the solution; see [about the two flows](#about-the-two-flows). |
| No decision email | The flow must be **On**, the request needs a valid requester email, and the settings JSON must keep every `{{placeholder}}`. Check **Decision notification status** and the error field on the request. |
| An email was marked **Needs review** | The send outcome was uncertain. Check Sent Items before resending; see [decision notifications](DECISION-NOTIFICATIONS.md#failure-and-retry-handling). |
| A reviewer can't open the app | Assign both **Basic User** and **Agent CoE Reviewer**, and check the Power Apps licence. |

## More information

- [Solution overview](SOLUTION-OVERVIEW.md)
- [Decision notifications](DECISION-NOTIFICATIONS.md)
- [Test prompts](TEST-PROMPTS.md)
- [Disclaimer and adopter responsibilities](../NOTICE.md)
- [Security reporting](../SECURITY.md)

This repository has no support SLA. When reporting an issue, remove tenant identifiers and personal data, and include the solution version and sanitized error text.
