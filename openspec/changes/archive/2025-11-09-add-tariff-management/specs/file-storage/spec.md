# File Storage

## ADDED Requirements

### Requirement: PDF File Upload

The system SHALL accept PDF file uploads for tariffs and store them in the configured uploads directory with organized structure.

#### Scenario: Upload PDF to tariff

- **WHEN** admin uploads 2MB PDF file for tariff "Fit Start"
- **THEN** system validates file is PDF format
- **AND** stores file in `uploads/tariffs/{tariff_id}/{unique_filename}.pdf`
- **AND** creates database record with tariff_id, filename, file_path, file_size
- **AND** returns file metadata with HTTP 201

#### Scenario: Upload oversized file

- **WHEN** admin uploads PDF exceeding configured MAX_UPLOAD_SIZE
- **THEN** system rejects with HTTP 413 and size limit message

#### Scenario: Upload non-PDF file

- **WHEN** admin uploads file with MIME type not application/pdf
- **THEN** system rejects with HTTP 400 and format error

#### Scenario: Upload to non-existent tariff

- **WHEN** admin uploads file for non-existent tariff UUID
- **THEN** system rejects with HTTP 404

### Requirement: File Retrieval

The system SHALL provide endpoints to list files for a tariff and retrieve individual file metadata.

#### Scenario: List files for tariff

- **WHEN** client requests files for tariff with 3 uploaded PDFs
- **THEN** system returns array of 3 file metadata objects with HTTP 200
- **AND** each object includes id, tariff_id, filename, file_size, created_at

#### Scenario: Get file by ID

- **WHEN** client requests file metadata by valid UUID
- **THEN** system returns file details with HTTP 200
- **AND** includes download URL or path

#### Scenario: Get file for non-existent tariff

- **WHEN** client requests files for non-existent tariff UUID
- **THEN** system returns empty array with HTTP 200

### Requirement: File Deletion

The system SHALL allow admin users to delete PDF files and remove both database records and physical files.

#### Scenario: Delete file by ID

- **WHEN** admin deletes file with valid UUID
- **THEN** system removes database record
- **AND** deletes physical file from uploads directory
- **AND** returns HTTP 204

#### Scenario: Delete non-existent file

- **WHEN** admin attempts to delete non-existent file UUID
- **THEN** system returns HTTP 404

#### Scenario: Delete file with missing physical file

- **WHEN** admin deletes file record where physical file is already missing
- **THEN** system removes database record
- **AND** logs warning about missing file
- **AND** returns HTTP 204

### Requirement: File Validation

The system SHALL enforce validation rules on uploaded files.

#### Scenario: Validate MIME type

- **WHEN** system receives file upload
- **THEN** checks Content-Type header is application/pdf
- **AND** optionally verifies PDF magic bytes

#### Scenario: Validate file size

- **WHEN** system receives file upload
- **THEN** checks file size does not exceed MAX_UPLOAD_SIZE from settings
- **AND** rejects before writing to disk if oversized

#### Scenario: Sanitize filename

- **WHEN** system receives file with name "../../../etc/passwd.pdf"
- **THEN** sanitizes filename to remove path traversal characters
- **AND** generates safe unique filename

### Requirement: Storage Configuration

The system SHALL load file storage settings from environment variables.

#### Scenario: Load upload directory path

- **WHEN** application starts
- **THEN** reads UPLOAD_DIR from environment
- **AND** defaults to "uploads" if not set

#### Scenario: Load size limits

- **WHEN** application starts
- **THEN** reads MAX_UPLOAD_SIZE_MB from environment
- **AND** converts to bytes for validation
- **AND** defaults to 10MB if not set

#### Scenario: Create upload directories

- **WHEN** application starts or first upload occurs
- **THEN** ensures `{UPLOAD_DIR}/tariffs/` directory exists
- **AND** creates with appropriate permissions
