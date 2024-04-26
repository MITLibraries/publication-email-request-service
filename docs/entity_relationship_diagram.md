# PERS Database Entity Relationship Diagram 

The Publication Email Request Service (PERS) relies on a database to keep track of the email requests that have been sent by stakeholders. Monitoring the email requests via database prevents duplication of email requests. The diagram describes the relationships between entities, or tables, in the database.

The relationships depicted in the diagram can be summarized as follows:
* A `Liaison` belongs to **one** `DLC`.
* A `DLC` is assigned to **one or more** authors.
* A `Publication (needing request)` can be associated with **one or more** `Author(s)`.
* A `Publication (needing request)` can only be included in **one** `Email`; an `Email` can include **one or more** `Publication(s)`.
* When an `Email` is created, it is assigned to **one** `Author` and **one** `Liaison`.

```mermaid
erDiagram
    publication["Publication (needing request)"]{
        string id PK 
        string title
        string citation
        string email_id FK
    }
    dlc[DLC]{
        string id PK
        string name
    }
    liaison[Liaison]{
        string id PK
        string first_name
        string last_name
        string email_address
        bool active
    }
    author[Author]{
        string id PK
        string dlc FK
        string email_address
        string first_name
        string last_name
    }
    email[Email]{
        string id PK
        richtext original_text
        richtext latest_text
        date date_sent
    }
    liaison }o--o| dlc: "belongs to"
    dlc ||--|{ author: has
    author }|--o{ publication: has
    publication }o--|| email: "included in"
    author ||--o{ email: receives
    liaison ||--o{ email: receives
```