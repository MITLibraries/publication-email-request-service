# Publication Email Request Service (PERS)

The following are sequence diagrams describing the workflow for sending publication email requests with this service. At high-level the steps involved are:

1. Import citations for authors
2. Create publication email requests
3. Review and (optionally) update emails
4. Send emails to Liaisons

## Import citations for authors 

```mermaid
sequenceDiagram
    autonumber
    participant user as User
    participant pers as Publication Email Request Service <br> (PERS)
    participant elements as Symplectic Elements
    participant pers_db as PERS Database
    user ->> pers: Select option to import citations
    pers ->> user: Request user input for author's Element's ID
    user -->> pers: Respond with selected author's Element's ID
    pers ->> elements: Send GET request to Elements API <br>to retrieve author data <br> "<ELEMENTS_ENDPOINT>users/{author_id}
    elements -->> pers: Author data XML string <br> ("Email", "First Name", "Last Name", "MIT ID", "DLC", "Start Date", "End Date")
    pers ->> pers: Parse XML string to AuthorRecord
    pers ->> pers_db: Upsert record to 'Author' table
    pers ->> elements: Send GET request to Elements API <br> to retrieve author's publications <br> <ELEMENTS_ENDPOINT>users/{author_id}/publications?&detail=full
    elements -->> pers: Author publications XML string
    pers ->> pers: Parse XML string to list of key-value pairs <br> for *qualifying* publications <br>(publication IDs and titles)

    Note over pers, elements: As PERS parses through the author publications XML string, <br> it runs a series of preliminary checks to determine if the publication meets the criteria <br> for an email request. If checks pass, the publication is added to a list.

    loop For every publication
        pers ->> elements: Send GET request to Elements API <br> to retrieve publication data <br> <ELEMENTS_ENDPOINT>publications/{publication_id}
        elements -->> pers: Publication citation data XML string
        pers ->> pers: Parse XML string to PublicationRecord
        pers -->> pers: Run checks on publication <br> 1.PublicationRecord is citable <br> 2. PublicationRecord has required identifiers <br> (MIT ID, Publication ID)
        pers ->> pers_db: Check if any records in the 'Email' table linked to the publication have been sent <br> (i.e., `PublicationRecord.id in Email.publications and Email.date_sent is not None`)
        pers ->> pers_db: Check if a record exists in the 'Publication' table where `Publication.id = PublicationRecord.id`.
        pers ->> pers_db: Upsert record to the 'Publication' table    
    end
```

## Create publication email requests

```mermaid
sequenceDiagram
    autonumber
    participant user as User
    participant pers as Publication Email Request Service <br> (PERS)
    participant elements as Symplectic Elements
    participant pers_db as PERS Database

    user ->> pers: Select from list of unsent citations <br> (records from 'Publications' table)
    loop For all authors linked to the selected publications
        pers ->> pers_db: Get records from the 'Publication' table where `Publication.id in selected list AND Publication.author = author.id`
        pers ->> pers_db: Get records from the 'Publication' table where `Publication.email.date_sent = Null`.
        pers_db -->> pers: Unsent record(s) from 'Publication' table
        pers ->> pers_db: Get the author from the unsent records
        pers_db -->> pers: Record from 'Author' table
        pers ->> pers_db: Get records from 'Email' table where `Email.author = author AND Email.date_sent = Null"
        pers_db -->> pers: Record(s) from 'Email' table
        break if author has more than one (>1) unsent email
            pers ->> user: Raise error
        end
        
        alt single (1) unsent email exists for author
            pers ->> pers: Rebuild citations list in email
            pers ->> pers_db: Update record in 'Email' table
        else no (0) unsent email exists for author 
            pers ->> pers: Create email for author
            pers ->> pers_db: Add record to 'Email' table
        end
    end
```

## Review and (optionally) update emails

```mermaid
sequenceDiagram
    autonumber
    participant user as User
    participant pers as Publication Email Request Service <br> (PERS)
    participant pers_db as PERS Database

    user ->> pers: Select option to evaluate emails
    pers ->> pers_db: Get records from 'Email' table <br> (`Email.date_sent = NULL`)
    pers_db -->> pers: Pending emails
    pers -->> user: List of unsent emails

    user ->> pers: Select pending email to review
    pers -->> user: Display text editor with content of pending email
    alt User updates content of pending email
        pers ->> pers_db: Update 'latest_text' field of record in 'Email' table
    end
```

## Send emails to Liaisons

```mermaid
sequenceDiagram
    autonumber
    autonumber
    participant user as User
    participant liaison as Liaison
    participant pers_admins as PERS Admins
    participant pers as Publication Email Request Service <br> (PERS)
    participant pers_db as PERS Database

    user ->> pers: Select option to list unsent email requests
    pers ->> pers_db: Get records from 'Email' table <br> where `Email.date_sent = NULL`)
    pers -->> user: Display list of drafted email requests
    user ->> pers: Select email requests to send <br> (mark checkbox next to email request in list)

    loop For every selected email
        pers ->> pers_db: Get record from 'Email' table <br> where `Email.id = ID of selected email`
        pers_db -->> pers: Record from 'Email' table
        pers ->> pers: Run checks on email <br> 1. Email.date_sent is NULL (not sent) <br> 2. Email.liaison is NOT NULL (assigned)
        
        alt if EMAIL_TESTING_MODE
            pers ->> pers_admins: Send email request
        else
            pers ->> liaison: Send email request <br> (cc Scholarly Communications Moira List)
        end
        pers ->> pers_db: Update record in 'Email' table <br> (Email.date_sent = current date [YYYY-MM-DD])
    end
```

