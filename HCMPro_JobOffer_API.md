Authentication

  First, authenticate to get a JWT token:
  POST http://localhost:3101/api/auth/login
  Content-Type: application/json

  {
    "email": "admin@acme.com",
    "password": "any_password"
  }

  Job Offer API Endpoints

  1. Get All Job Offers

  GET http://localhost:3101/api/job-offers
  Authorization: Bearer <your_jwt_token>

  # With filtering and pagination
  GET http://localhost:3101/api/job-offers?status=SENT&page=1&l
  imit=10&search=developer

  2. Get Job Offer by ID

  GET http://localhost:3101/api/job-offers/{id}
  Authorization: Bearer <your_jwt_token>

  3. Create New Job Offer

  POST http://localhost:3101/api/job-offers
  Authorization: Bearer <your_jwt_token>
  Content-Type: application/json

  {
    "positionId": "position-uuid",
    "candidateName": "John Doe",
    "candidateEmail": "john@example.com",
    "candidatePhone": "+1234567890",
    "jobTitle": "Senior Developer",
    "departmentId": "dept-uuid",
    "managerId": "manager-uuid",
    "employmentType": "FULL_TIME",
    "workLocation": "HYBRID",
    "startDate": "2024-02-01T00:00:00.000Z",
    "salary": 75000,
    "currency": "USD",
    "expirationDate": "2024-01-15T00:00:00.000Z"
  }

  4. Update Job Offer

  PUT http://localhost:3101/api/job-offers/{id}
  Authorization: Bearer <your_jwt_token>
  Content-Type: application/json

  {
    "salary": 80000,
    "startDate": "2024-02-15T00:00:00.000Z"
  }

  5. Workflow Actions

  Send Offer to Candidate:
  POST http://localhost:3101/api/job-offers/{id}/send
  Authorization: Bearer <your_jwt_token>

  Approve Offer:
  POST http://localhost:3101/api/job-offers/{id}/approve
  Authorization: Bearer <your_jwt_token>

  Accept Offer (Candidate Response):
  POST http://localhost:3101/api/job-offers/{id}/accept
  Authorization: Bearer <your_jwt_token>

  Reject Offer:
  POST http://localhost:3101/api/job-offers/{id}/reject
  Authorization: Bearer <your_jwt_token>
  Content-Type: application/json

  {
    "rejectionReason": "Salary expectations not met"
  }

  Convert to Employee:
  POST
  http://localhost:3101/api/job-offers/{id}/convert-to-employee
  Authorization: Bearer <your_jwt_token>

  Query Parameters

  - status: Filter by offer status (DRAFT, SENT, APPROVED,
  ACCEPTED, etc.)
  - departmentId: Filter by department
  - employmentType: Filter by employment type
  - search: Search in candidate name, email, or job title
  - page: Page number for pagination
  - limit: Number of results per page
  - sortBy: Sort field (createdAt, salary, startDate)
  - sortOrder: Sort direction (asc, desc)

  Example Response

  {
    "jobOffers": [
      {
        "id": "offer-uuid",
        "candidateName": "John Doe",
        "candidateEmail": "john@example.com",
        "jobTitle": "Senior Developer",
        "status": "SENT",
        "salary": 75000,
        "currency": "USD",
        "startDate": "2024-02-01T00:00:00.000Z",
        "offerDate": "2024-01-01T00:00:00.000Z",
        "expirationDate": "2024-01-15T00:00:00.000Z",
        "position": {
          "title": "Senior Developer",
          "department": {
            "name": "Engineering"
          }
        }
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 10,
      "total": 25,
      "pages": 3
    }
  }
