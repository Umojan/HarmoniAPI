# tariff-management Specification

## Purpose
TBD - created by archiving change add-tariff-management. Update Purpose after archive.
## Requirements
### Requirement: Tariff Creation

The system SHALL allow admin users to create new tariff plans with name, description, calories, features, and base price.

#### Scenario: Create tariff with valid data

- **WHEN** admin submits tariff data with name "Fit Start", description "Beginner plan", calories 1500, features list, and price 2990
- **THEN** system creates tariff record with UUID and timestamps
- **AND** returns created tariff with HTTP 201

#### Scenario: Create tariff with duplicate name

- **WHEN** admin submits tariff with existing name
- **THEN** system rejects with HTTP 400 and error message

#### Scenario: Create tariff with invalid price

- **WHEN** admin submits tariff with negative or zero price
- **THEN** system rejects with HTTP 422 validation error

### Requirement: Tariff Retrieval

The system SHALL provide endpoints to retrieve all tariffs or a specific tariff by ID.

#### Scenario: List all tariffs

- **WHEN** client requests tariff list
- **THEN** system returns array of all tariffs with HTTP 200
- **AND** each tariff includes id, name, description, calories, features, price, timestamps

#### Scenario: Get tariff by ID

- **WHEN** client requests tariff by valid UUID
- **THEN** system returns tariff details with HTTP 200
- **AND** includes associated file references

#### Scenario: Get non-existent tariff

- **WHEN** client requests tariff with non-existent UUID
- **THEN** system returns HTTP 404 with error message

### Requirement: Tariff Update

The system SHALL allow admin users to update tariff fields including name, description, calories, features, and price.

#### Scenario: Update tariff name and price

- **WHEN** admin updates tariff with new name "Balance Pro" and price 3490
- **THEN** system updates record and updated_at timestamp
- **AND** returns updated tariff with HTTP 200

#### Scenario: Update non-existent tariff

- **WHEN** admin attempts to update non-existent tariff ID
- **THEN** system returns HTTP 404

### Requirement: Tariff Deletion

The system SHALL allow admin users to delete tariff plans and cascade delete associated files.

#### Scenario: Delete tariff with files

- **WHEN** admin deletes tariff that has 2 attached PDF files
- **THEN** system deletes tariff record
- **AND** deletes all associated file records
- **AND** deletes physical PDF files from uploads directory
- **AND** returns HTTP 204

#### Scenario: Delete non-existent tariff

- **WHEN** admin attempts to delete non-existent tariff ID
- **THEN** system returns HTTP 404

### Requirement: Tariff Data Validation

The system SHALL enforce validation rules on tariff fields.

#### Scenario: Validate required fields

- **WHEN** admin submits tariff without name
- **THEN** system returns HTTP 422 with field error

#### Scenario: Validate data types

- **WHEN** admin submits calories as string instead of integer
- **THEN** system returns HTTP 422 with type error

#### Scenario: Validate constraints

- **WHEN** admin submits name exceeding 255 characters
- **THEN** system returns HTTP 422 with length constraint error

