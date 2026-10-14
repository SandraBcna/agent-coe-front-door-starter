# Requester decision notifications

The unmanaged solution includes **CAT - Notify Requester of CoE Decision**. It sends a requester email when an existing intake request's approval status is changed to **Approved** or **Rejected**. It is the only notification in the template. The conversational agent has no notification tool and does not decide whether to send it.

**Status:** the flow ships Off. Do not enable it in a production environment until the acceptance checks below pass.

## Behaviour

| Event | Result |
|---|---|
| New, Tracked, In Review, or build-stage change | No decision email |
| First Approved decision | Approval email and a persisted send receipt |
| First Rejected decision | Rejection email and a persisted send receipt |
| Save the same decision again | No duplicate email |
| Approved changes to Rejected, or the reverse | One new email for the new decision |
| Approved changes to In Review and back to Approved without an intervening notified rejection | No repeat approval email |
| An old queued event no longer matches the current saved decision | Skip the obsolete notification |
| Missing/invalid email or settings | No email; record Failed with diagnostic context |
| A send fails or its outcome cannot be confirmed | Record Needs review; do not resend automatically |

The trigger monitors updates to `cat_status` only, filtered to Approved (`100000003`) and Rejected (`100000004`). Runs are serialized. The flow reads the current record and compares its decision with `cat_lastnotifieddecision` before sending.

## Request fields

| Field | Use |
|---|---|
| Requester email (`cat_requesteremail`) | Exactly one confirmed work email; collected from verified signed-in context or confirmed during intake, never inferred from a shared maker/owner identity |
| Comments shared with requester (`cat_decisioncomments`) | Explicitly requester-facing CoE comments; never put internal-only review notes here |
| Next step (`cat_proposednextactions`) | Guidance the CoE intends to share; when blank, the selected template's default guidance is used |
| Last notified decision (`cat_lastnotifieddecision`) | Last decision the email connector accepted; suppresses duplicate notifications |
| Decision notification status (`cat_notificationstatus`) | Not sent, Sending, Sent, Failed, or Needs review |
| Decision notification sent on (`cat_notificationsenton`) | UTC timestamp for the latest accepted send |
| Decision notification error (`cat_notificationerror`) | Operator diagnostic and flow run reference |

The intake main form exposes these fields. Receipt fields are read-only on that form and must be workflow-owned in the organization's security design. CoE reviewers must save requester-facing comments and next-step guidance **before or together with** changing the decision. A later comment-only edit does not send another email. The dashboard's status controls trigger the same flow, but comments are maintained on the request form.

## Target configuration

The flow ships **Off**. Configure it only in the intended target environment.

1. Bind `cat_decisionnotifications_dataverse` to an approved Dataverse connection with the required request Read/Write, environment-variable Read, and trigger-registration permissions.
2. Bind `cat_decisionnotifications_outlook` to an approved Office 365 Outlook connection. Its mailbox is the sender; a shared mailbox requires a deliberately configured and separately tested sending action.
3. In the solution's environment variable **Agent CoE decision notification settings** (`cat_DecisionNotificationSettings`), set one target-owned **current value**. Keep identities, mailbox addresses, and current values outside the repository and release ZIP.
4. Obtain approval for the templates, requester-facing comments, recipient handling, CoE contact, DLP, connector licensing, and sender mailbox.
5. Turn the flow on from the solution (**Cloud flows** > select the flow > **Turn on**) in a non-production environment and complete the acceptance checks. Don't save or publish it in a designer; that removes its secured inputs and no-retry email send (see [about the two flows](INSTALLATION.md#about-the-two-flows)). Leave the exported/distributed flow Off.

The JSON settings contain:

```json
{
  "coeContact": "[APPROVED COE CONTACT]",
  "approval": {
    "subject": "{{request_reference}} - request approved",
    "body": "<p>Request {{request_reference}} ({{request_name}}) has been {{decision}}.</p><p>Route: {{route}}</p><p>Next step: {{next_step}}</p><p>CoE comments: {{comments}}</p>{{request_summary}}<p>Questions: {{coe_contact}}</p>",
    "defaultNextStep": "[APPROVED NEXT STEP AFTER APPROVAL]"
  },
  "rejection": {
    "subject": "{{request_reference}} - request rejected",
    "body": "<p>Request {{request_reference}} ({{request_name}}) has been {{decision}}.</p><p>Next step: {{next_step}}</p><p>CoE comments: {{comments}}</p>{{request_summary}}<p>Questions: {{coe_contact}}</p>",
    "defaultNextStep": "[APPROVED NEXT STEP AFTER REJECTION]"
  }
}
```

Replace bracketed content in the target, not in Git. Each body must retain every documented placeholder (`{{route}}` is required only in the approval body); the flow fails explicitly rather than send an incomplete decision message. Request text and comments are HTML-escaped, and line breaks are preserved. Subjects have CR/LF removed. Templates are trusted organization-approved HTML, not requester-provided content.

`{{request_summary}}` is a short, HTML-escaped list built from the request's business problem, requested outcome, target users, expected users, and submission date. Empty fields are omitted, and long text is truncated to 500 characters. The email never contains a link to the Dataverse record or the CoE app, so requesters need no access to them. Internal fields, such as governance zone, data sources, and the source conversation, are never included.

For approvals, `{{next_step}}` uses the request's **Next step** (`cat_proposednextactions`) when filled in, otherwise the approval `defaultNextStep`. The agent drafts that field at intake in requester-friendly words; reviewers should check it before approving. For rejections, the email never shows a route and always uses the rejection `defaultNextStep`, so guidance left over from an earlier approval cannot reach the requester. Put any rejection-specific guidance in **Comments shared with requester**.

## Failure and retry handling

**Sent means accepted by the email connector, not guaranteed inbox delivery.** Verify the mailbox and delivery separately. There is no atomic transaction between sending an Outlook email and updating Dataverse; the solution does not claim exactly-once delivery.

Before sending, the flow records **Sending**. Only a successful email action writes **Sent**, the UTC timestamp, and the last notified decision. Email-action automatic retries are disabled. A failed send, timeout, or failure to persist the receipt is treated conservatively: **Sending** or **Needs review** blocks another automatic attempt.

For **Failed** before a send, correct the recipient/configuration and resubmit the failed run while its decision is still current. For **Needs review** or a stranded **Sending**, an authorized operator must inspect the flow run, sender Sent Items, and recipient delivery. If accepted, reconcile the receipt without sending again. Only if non-delivery is established may the operator reset the attempt state and resubmit. Do not clear the last notified decision blindly.

An inaccessible request or unavailable Dataverse service can prevent recording an error on that row; the flow run must still fail and be monitored. Restrict run-history access because it contains requester email and decision content.

## Acceptance checks

Use only approved test mailboxes and synthetic TEST requests. Keep received messages, flow outcomes, and Dataverse receipt values as private test records outside this repository.

| Check | Pass condition |
|---|---|
| Approved | One actual email with reference/name, approval, route/next step, CoE comments/contact, and request summary; no record link |
| Rejected | One actual email with reference/name, rejection, the template's rejection next step, CoE comments/contact, and request summary; no route, no stored approval guidance, no record link |
| Same decision saved again | No additional message or receipt timestamp change |
| Approved -> Rejected -> Approved | Three decision messages in total, latest receipt matches Approved |
| New/In Review/Tracked/build-only/comment-only updates | No decision email |
| Missing/multiple/invalid requester addresses | No send; Failed is visible |
| Missing/invalid settings or required template tokens | No send; explicit failure is visible |
| Organization customization | Both customized templates and default next-step guidance appear in the received emails |
| Special characters | Request names/comments display literally, not as HTML or replacement placeholders |
| Send failure / ambiguous outcome | Needs review or Sending blocks blind reruns; no false Sent receipt |
| Request summary | Shows recorded summary fields literally, omits empty fields, and contains no Dataverse or app link |
| Portability | Final unmanaged ZIP imports into an empty environment with both flows Off and no target values |

See [NOTICE.md](../NOTICE.md) for the unchanged as-is disclaimer and adopter responsibilities.
