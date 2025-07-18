# Aidbox configuration

## Local development
Create .env file and specify your aidbox license
```
cp .env.tpl .env
```
Run aidbox and otehr components with docker
```
docker compose up
```

## Tutorials

### Delete data of any user

The patient user in the system owns the following resources: User, Role, Patient, and QuestionnaireResponse.
To delete these resources, we first need to obtain the patient's ID. Then, we execute SQL commands to remove the associated data.

This is a step-by-step guide on how to delete all related resources for a specific user using Aidbox's DB console.

**Short description:** Retrieve the patient's ID and email, then run SQL commands to filter and delete the corresponding resources from the database.

#### 1. Get user IDS, phones and email

```sql
SELECT
    id AS ID,
    (
        SELECT t->>'value'
        FROM jsonb_array_elements(resource->'telecom') AS t
        WHERE t->>'system' = 'email'
        LIMIT 1
    ) AS email,
    (
        SELECT t->>'value'
        FROM jsonb_array_elements(resource->'telecom') AS t
        WHERE t->>'system' = 'phone'
        LIMIT 1
    ) AS phone
FROM patient
WHERE "patient".resource::text ILIKE '%YOUR_SEARCH_STRING%';
```

Replace **YOUR_SEARCH_STRING** to find a patient with any information, ex: email, name, etc...

#### 2. Delete user

```sql
DELETE FROM "user"
WHERE resource#>>'{email}' = 'USER_EMAIL';
```

#### 3. Delete user role

```sql
DELETE FROM role
WHERE resource#>>'{links,patient,id}' = 'PATIENT_ID';
```

#### 4. Delete user patient

```sql
DELETE FROM patient
WHERE id = 'PATIENT_ID';
```

#### 5. Delete user questionnaire responses

```sql
DELETE FROM QuestionnaireResponse
WHERE resource#>>'{subject,id}' = 'PATIENT_ID';
```

#### Example of all commands with known patient's ID and email

```sql
DELETE FROM "user" WHERE resource#>>'{email}' = 'USER_EMAIL';
DELETE FROM role WHERE resource#>>'{links,patient,id}' = 'PATIENT_ID';
DELETE FROM patient WHERE id = 'PATIENT_ID';
DELETE FROM QuestionnaireResponse WHERE resource#>>'{subject,id}' = 'PATIENT_ID';
```

### Create new coordinators

To create a coordinator, you need to add two entities to the system: User and Role.

Below, you will find links to create them in the Aidbox console, along with information about the required fields and which values you need to modify to ensure each coordinator is unique and valid.

Please note that the order of creation is important, as there are dependencies between the resources.

In this document aidbox backend reference is http://localhost:8080. You need to use correct address.

#### 1. Create User resource

Use this link:

```bash
http://localhost:8080/ui/console#/resource-types/User/new?tab=raw&create=true&raw-format=json
```

```json
{
  "password": "password",
  "id": "my-custom-coordinator",
  "resourceType": "User",
  "email": "admin@pro.com"
}
```

**Important notes:**

1. Don't forget to use a strong password;
2. You can use any id or just skip it.

#### 2. Create Role resource

Use this link:

```bash
http://localhost:8080/ui/console#/resource-types/Role/new?tab=raw&create=true&raw-format=json
```

```json
{
  "name": "admin",
  "user": {
    "reference": "User/my-custom-coordinator"
  },
  "links": {
    "organization": {
      "reference": "Organization/mammochat"
    }
  },
  "id": "my-custom-coordinator",
  "resourceType": "Role"
}
```

**Important notes:**

1. Use need to use a reference to your previously created User ID;
2. You can use any id or just skip it.

### Request patient's data through FHIR API

You can retrieve data for a specific user by searching for the Patient resource by ID, along with related QuestionnaireResponse resources using the _revinclude search parameter. This approach will return a Bundle of type searchset, which should contain a single Patient resource and three QuestionnaireResponse resources.

Below is an example of such a request. You can use Aidbox's REST console to execute it.

```bash
GET /fhir/Patient?_id=patient_id&_revinclude=QuestionnaireResponse:subject
content-type: application/json
accept: application/json
```