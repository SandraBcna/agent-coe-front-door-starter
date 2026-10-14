# Notice and disclaimer

## Status

Agent CoE Front Door is an independent reusable reference template for evaluation and adaptation. Version 1.0.0.0 (release v1.0.0) must be installed and tested in a non-production environment before any production use. Power Platform inventory and decision notification email require target-specific authentication, configuration, and acceptance tests.

## No Microsoft endorsement or support commitment

This repository is not an official Microsoft product, endorsed reference architecture, certification, or commitment of Microsoft support. Microsoft product names identify dependencies only.

Nothing in this repository changes Microsoft Product Terms, licensing requirements, service limits, security boundaries, privacy obligations, or an organization's agreements with Microsoft.

## No warranty

The software and documentation are provided **as is**, without warranty or guarantee of accuracy, availability, security, compliance, fitness, or suitability for a particular purpose. Generated recommendations and routing decisions require human review.

## Adopter responsibilities

Before any deployment, adopters must independently:

- verify ownership and permission to use all knowledge and data;
- replace organization placeholders with approved content;
- configure approved identities, connections, destinations, and channels;
- apply least-privilege Dataverse and application access;
- review licensing, capacity, DLP, privacy, security, accessibility, and compliance;
- test with representative authorized and unauthorized users;
- verify notification recipient and message behavior;
- establish monitoring, support, incident response, lifecycle, and change control; and
- complete production-readiness and risk approval under their own policies.

## Data and confidentiality

Do not commit or upload credentials, tokens, connection secrets, customer data, live catalogue or request data, internal reference documents, private document links, restricted information, or sensitive screenshots.

The release contains connector definitions and unbound connection references only. Native connection authentication is configured by the adopting organization's owners in its target services, never embedded in this repository or solution ZIP. Repository access controls do not make it an approved credential store. If authentication storage or an access boundary cannot be approved and verified, leave the affected integration disabled and the agent unshared.

This notice does not authorize disclosure, override a sensitivity label, replace an information-protection policy, or make restricted material safe to share.

## Known deployment considerations

- Target-native recreation of the Dataverse MCP tool and connection may be required.
- Knowledge retrieval must be tested even when sources show Ready.
- The package includes no knowledge files or organization SharePoint source. Keep repository KB-01, KB-02, and KB-03 templates out of the agent until locally approved; attach approved sources and remove any inherited placeholder left by an older unmanaged import.
- Power Platform inventory remains disabled until a target Entra application owner configures the connector and an administrator grants delegated consent.
- Approval and rejection email remains disabled until target-owned Dataverse/Outlook connections, templates, requester addresses, CoE contact, permissions, and actual delivery have been verified.
- Email-service acceptance is not guaranteed inbox delivery; ambiguous send outcomes require operator review before retrying.
- With instruction discovery on, the agent shares only an AI-generated summary, and its Dataverse connection must not be able to read the raw definitions. Native instruction-bearing authoring definitions require approved source access and protected Dataverse columns; they are not supplied by inventory alone or guaranteed published runtime prompts.
- No test agents or test business data are included in the solution package. Only the actual Agent CoE Front Door agent and required components are distributed.
- UX Agent Project support can vary by tenant.
- Unmanaged solution imports do not remove obsolete components.
- Production behavior depends on target configuration, identity, permissions, licensing, capacity, and service availability.
