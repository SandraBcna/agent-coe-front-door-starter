# User stories

These user stories describe the reusable business scenarios that adopters should validate after importing and configuring the solution. Replace example policy, routing, and catalogue details with approved organizational content before using them for acceptance.

Stories map to the three personas in the [setup guide](INSTALLATION.md#three-personas): employees and makers chat with the agent, CoE reviewers use the triage app, and the admin sets up the solution. Stories about instruction content apply only when the optional instruction-discovery add-on is enabled.

The additional scenarios below are design and acceptance ideas, not claims that every behavior is implemented or has passed release validation.

## Employee describing a need without choosing a tool

As an employee, I want to explain the outcome I need in everyday language, so that I can receive a practical next step without knowing whether I need an agent, a template, or CoE help.

Acceptance criteria to validate:

- The response reflects the business outcome before recommending a route.
- The agent asks only for information needed to make the next recommendation.
- If the configured guidance cannot determine a route, the agent says so and points to an approved human contact.

## Employee looking for an existing agent

As an employee with a business need, I want the front door to check the agent catalogue and the tenant inventory before asking me to submit a new request, so that I can reuse an existing solution when one is available.

Acceptance criteria:

- The catalogue and, when enabled, the tenant inventory are checked before a new intake is proposed.
- A relevant existing agent is recommended when one is available. A published agent that is only in the inventory is labelled as not reviewed by the CoE, with a short description of what it does and never its instructions, owner or identifiers.
- Draft, quarantined or blocked agents are never revealed.
- A new intake is not created unless the user asks for further help or no suitable option exists.
- Any catalogue gap is stated clearly rather than invented.

## Employee comparing an existing option with a new request

As an employee, I want to understand why an existing agent might meet my need before requesting another build, so that I can make an informed choice.

Acceptance criteria to validate:

- The agent explains the relevant match and any known limitations using catalogue information.
- It does not imply that an unverified catalogue item is approved for my use.
- If the existing option is unsuitable, it offers the configured next route without inventing a new record.

## Employee asking a policy or licensing question

As an employee, I want the front door to answer licensing, governance, and naming questions from approved organizational knowledge, so that I can make the right next-step decision without raising an unnecessary ticket.

Acceptance criteria:

- The answer is grounded in the correct approved knowledge source.
- Local gaps, approval requirements, or escalation paths are disclosed.
- The agent does not invent entitlement, policy, or approval decisions.
- No intake record is created unless the user requests one.

## Maker seeking guided self-build

As a maker, I want the front door to guide me toward approved build patterns, templates, and governance steps, so that I can self-serve safely when CoE delivery is not required.

Acceptance criteria:

- The response includes the approved build path and governance checks.
- The response explains when to come back for CoE review or support.
- A concrete agreed self-build is logged as Tracked only after the user confirms the summary; pure how-to questions do not create a record.

## Maker finding an approved starting point

As a maker, I want guidance toward an approved template or build approach and the checks needed before sharing, so that I can turn a suitable idea into a responsible self-build.

Acceptance criteria to validate:

- The recommendation uses configured, approved guidance rather than assuming a template exists.
- Ownership, access, data handling, and review requirements are described where configured.
- Scenarios outside the self-build rules are routed to review instead of being treated as approved.

## Business sponsor requesting CoE support

As a business sponsor, I want to describe the business problem, users, timeline, and expected outcomes, so that the CoE receives enough structured information to triage the request.

Acceptance criteria:

- Only missing facts are requested.
- The agent summarizes the request before writing.
- The user must explicitly confirm before an intake record is created.
- The created record contains the intended values and can be read back.

## Sponsor correcting intake details

As a sponsor, I want to amend or cancel the proposed request after reviewing its summary, so that inaccurate details are not submitted.

Acceptance criteria to validate:

- Corrections are reflected in a new summary before any write.
- Cancelling the flow creates no intake record.
- A record is created only after a clear confirmation of the final summary.

## CoE reviewer managing demand

As a CoE reviewer, I want intake and catalogue records to appear in a triage app, so that I can review, filter, update, and manage demand consistently.

Acceptance criteria:

- The triage app opens for licensed, authorized users.
- Catalogue and intake navigation, views, forms, search, and filters work.
- Unauthorized users cannot access restricted records.
- Status and ownership changes follow the adopting organization's process.

## CoE reviewer searching actual instruction content

As an authorized CoE reviewer, I want to read agents' actual instruction-bearing definitions in the triage app, while employees only see a short summary of what each agent does.

Acceptance criteria:

- The inventory API's character count is not misrepresented as instruction text.
- Only approved source environments are queried with authorized Dataverse access.
- Native JSON/OBI definitions retain their source format, version, retrieval time, and actual availability.
- A relevant term absent from the name but present in the AI summary can be discovered in chat; the agent never queries the definition column.
- Raw definitions and run-history payloads remain protected and cannot override the Front Door agent's instructions or local policy.
- Missing mappings, denied reads, unsupported storage, and stale/empty definitions do not become invented capability claims.
- Catalogue approval is checked before calling an agent approved.

## CoE reviewer distinguishing decision from delivery

As a reviewer, I want to track the review outcome separately from delivery progress, so that a governance decision is not mistaken for a completed build.

Acceptance criteria to validate:

- The configured triage process defines what each status means.
- Review and delivery changes are visible to authorized reviewers.
- Reporting does not treat an approved idea as a delivered solution.

## Requester receiving a CoE decision

As a requester, I want an automatic email when the CoE approves or rejects my request, so that I know the decision and the next step.

Acceptance criteria:

- A change to Approved or Rejected sends to the confirmed requester email, not the shared maker or record owner.
- The email contains the request reference/name, decision, next step, requester-facing CoE comments, and CoE contact. Approval emails also show the route; rejection emails show no route and always use the organization's rejection next step.
- Instead of a link to the Dataverse record, the email includes a short request summary (business problem, requested outcome, target and expected users, submission date).
- Repeated saves of the same notified decision do not resend; a change to the opposite decision notifies again.
- The request records the send outcome and timestamp; a failed or ambiguous delivery is not reported as Sent.
- The organization can customize both templates and default next-step guidance without editing the flow.
- Actual received messages, duplicate guards, failure handling, and template changes pass the [notification acceptance checks](DECISION-NOTIFICATIONS.md).

## Operations owner preparing production use

As an operations owner, I want ownership, support, monitoring, knowledge review, access review, and connection renewal responsibilities assigned before launch, so that the front door has a sustainable operating model.

Acceptance criteria:

- Business, technical, security, knowledge, email, and support owners are documented.
- Capacity and support routes are defined.
- Knowledge and access review dates are recorded.
- Known limitations and rollback expectations are accepted before release.
