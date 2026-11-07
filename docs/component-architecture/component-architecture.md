# Component Architecture – Rock Starz

## 1. Introduction

The Rock Starz platform is designed as a web-based student mentoring and career guidance system. It connects students with suitable mentors, supports mentoring requests and relationships, and provides administrative facilities for managing users and monitoring platform activity.

The system follows a layered architecture consisting of a React-based frontend, a FastAPI backend, a PostgreSQL relational database, background processing components, and development and quality assurance tools.

The architecture separates user-facing interfaces, application logic, data access, and database storage. This separation supports modular development, easier maintenance, independent testing, and future enhancements.

## 2. Architecture Overview

The application is organized into the following major components:

1. Frontend – React, Vite and Tailwind CSS.
2. Backend – FastAPI and Python.
3. Application Services – Independent services handling specific business responsibilities.
4. Data Access Layer – SQLAlchemy ORM, repositories and database models.
5. Database – PostgreSQL with 12 relational tables.
6. Background Processing – Request expiry and notification generation.
7. Application Support – Environment configuration, logging and error handling.
8. Development and Quality Assurance – Postman, Pytest, GitHub and GitHub Actions.

### 2.1 Component Architecture Diagram

The following diagram illustrates the major components, their responsibilities, and their interactions.

![Component Architecture Diagram](component-architecture.png)

The frontend communicates with the backend through HTTPS using JSON-based API requests. The backend processes requests through its API and application service layers, accesses persistent data through the data access layer, and interacts with the PostgreSQL database.

Background processing handles time-dependent operations, while the development and quality assurance components support testing and continuous integration.

## 3. Frontend Architecture

### 3.1 Technology Stack

- React – Component-based frontend development.
- Vite – Development server and build tooling.
- Tailwind CSS – Utility-first styling framework.
- React Router – Client-side navigation and route management.

The frontend provides separate role-based portals for students, mentors, and administrators. Each portal exposes functionality relevant to its respective user role.

### 3.2 Role-Based Portals

**A. Student Portal**

The Student Portal allows students to access mentoring and career guidance facilities.

Its responsibilities include:

- Student profile management.
- Mentor discovery.
- Searching and filtering mentors.
- Sending and managing mentoring requests.
- Accessing the mentoring dashboard.
- Viewing relevant mentoring information.

**B. Mentor Portal**

The Mentor Portal provides mentors with facilities to manage their mentoring activities.

Its responsibilities include:

- Mentor profile management.
- Receiving and viewing mentoring requests.
- Accepting or rejecting requests.
- Managing assigned mentees.
- Accessing mentoring relationship information.

**C. Admin Portal**

The Admin Portal provides administrative facilities for monitoring and managing the platform.

Its responsibilities include:

- User management.
- Monitoring platform participation.
- Accessing reports and statistics.
- Viewing aggregated information about mentoring activities.

### 3.3 Shared UI Layer

The three portals use a shared frontend infrastructure layer.

It consists of:

- **React Router:** Handles navigation between application pages and portals.
- **Authentication Context:** Maintains authentication-related frontend state.
- **API Client:** Provides a common mechanism for communicating with backend APIs.
- **Protected Routes:** Restricts access to application routes based on authentication and authorization requirements.

The shared layer avoids unnecessary duplication of common frontend functionality.

## 4. Backend Architecture

### 4.1 Technology Stack

- Python – Backend programming language.
- FastAPI – Backend web framework.
- Pydantic – Request and data validation.
- JWT – Token-based authentication.
- RBAC – Role-Based Access Control.
- SQLAlchemy – Object-relational mapping and database interaction.
- PostgreSQL – Relational database management system.

The backend exposes versioned REST API endpoints under `/api/v1`.

### 4.2 API Router and Authentication Layer

The API Router acts as the primary entry point for frontend requests.

Its responsibilities include:

- Receiving HTTP requests from the frontend.
- Routing requests to the appropriate application service.
- Handling authentication using JWT.
- Enforcing role-based access control.
- Validating incoming request data.
- Using Pydantic models for request and response validation.

The API layer separates request handling and access control from the actual business logic implemented by application services