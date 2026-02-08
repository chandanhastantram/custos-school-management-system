# CUSTOS School Management System - Frontend Development Prompt

## Project Overview

**CUSTOS** (Custom Universal School Tracking & Operations System) is a comprehensive multi-tenant SaaS school/university management platform. Build a modern React/Next.js frontend that consumes the FastAPI backend at `http://localhost:8000/api/v1`.

---

## 🏗️ Technical Architecture

### Stack Requirements

- **Framework**: Next.js 14+ (App Router) with TypeScript
- **State Management**: TanStack Query (React Query) for server state, Zustand for client state
- **UI Library**: shadcn/ui + Tailwind CSS
- **Forms**: React Hook Form + Zod validation
- **Icons**: Lucide React
- **Charts**: Recharts or Chart.js

### Multi-Tenancy Pattern

Each school is a **tenant**. All API requests must include:

```http
X-Tenant-ID: {uuid}
Authorization: Bearer {access_token}
```

Login flow:

1. User enters school slug → `GET /tenants/by-slug/{slug}` returns branding
2. User submits email/password → `POST /auth/login` with `X-Tenant-ID` header
3. Store tokens, redirect to role-based dashboard

---

## 🔐 Authentication System

### Endpoints

| Endpoint                | Method | Description                                                |
| ----------------------- | ------ | ---------------------------------------------------------- |
| `/auth/login`           | POST   | Login, returns `{access_token, refresh_token, expires_in}` |
| `/auth/refresh`         | POST   | Refresh access token                                       |
| `/auth/logout`          | POST   | Revoke tokens                                              |
| `/auth/me`              | GET    | Get current user info                                      |
| `/auth/change-password` | POST   | Change password                                            |

### JWT Token Structure

```typescript
interface TokenPayload {
  sub: string; // user_id
  tenant_id: string;
  email: string;
  roles: string[];
  permissions: string[];
  exp: number;
}
```

---

## 👥 User Roles & Dashboards

Build **6 role-based dashboard experiences**:

| Role            | Dashboard Features                                  |
| --------------- | --------------------------------------------------- |
| **super_admin** | Full platform control, all modules, user management |
| **principal**   | School-wide analytics, staff management, approvals  |
| **sub_admin**   | Administrative tasks, scheduling, registrations     |
| **teacher**     | Class management, grading, lesson plans, attendance |
| **student**     | Assignments, results, timetable, activity tracking  |
| **parent**      | Child's progress, fees, communications              |

### Route Structure

```
/login                    # Tenant slug + credentials
/dashboard               # Role-based redirect
/admin/*                 # super_admin, principal, sub_admin
/teacher/*               # Teacher-specific views
/student/*               # Student portal
/parent/*                # Parent portal
```

---

## 📚 Core Modules to Implement

### 1. User Management (`/users`)

- CRUD for users, students, teachers
- Role assignment interface
- Bulk import functionality

### 2. Academic Structure (`/academic`)

- Academic years, classes, sections
- Subjects and curriculum
- Teaching assignments (teacher ↔ class ↔ subject)

### 3. Scheduling (`/scheduling`)

- Timetable builder with drag-drop
- Period/slot management
- Schedule conflict detection

### 4. Attendance (`/attendance`)

- Mark single/bulk attendance
- Calendar view per student
- Leave request workflow
- Teacher attendance tracking

### 5. Finance (`/finance`)

- Fee components configuration
- Fee structures per class/year
- Invoice generation
- Payment recording + receipts
- Dues and collection reports

### 6. Payments (`/payments`)

- Payment gateway integration (Razorpay)
- Order creation → Payment → Verification flow
- Refund processing

### 7. Examinations (`/examinations`)

- Exam creation and scheduling
- Student registration with eligibility check
- Hall ticket generation/download
- Result entry and publication
- Revaluation applications

### 8. Analytics (`/analytics`)

**CRITICAL**: Role-based data visibility:

- **Students**: Only see own activity score, NO actual scores, NO class comparison
- **Parents**: Only child's activity score
- **Teachers**: Class aggregate + individual students (no ranking)
- **Admin/Principal**: Full analytics with comparisons

### 9. Helpdesk (`/helpdesk`)

- Support ticket system with categories
- Transcript applications
- Grace mark applications
- FAQ management

### 10. Feedback & Surveys (`/feedback`)

- Survey builder with multiple question types
- Survey distribution to classes
- Response collection
- Results aggregation (for faculty review)

### 11. Messaging (`/messages`)

- Internal inbox system
- Circulars and announcements
- Threaded conversations

### 12. Calendar (`/calendar`)

- School events calendar
- Academic calendar integration
- Personal schedules

### 13. AI Features (`/ai`)

- Question generation
- Lesson plan generation
- OCR for document scanning
- Doubt solver (student-facing)

---

## 🎨 UI/UX Requirements

### Design System

- **Colors**: Support tenant-specific primary color from `/tenants/current`
- **Dark Mode**: Required toggle
- **Responsive**: Mobile-first, works on tablets/phones

### Component Patterns

```tsx
// Standard list page pattern
<DataTable
  columns={columns}
  data={data}
  pagination
  filters={[statusFilter, searchFilter]}
  actions={[create, export]}
/>

// Standard form pattern
<Form onSubmit={handleSubmit}>
  <FormField name="..." control={...} />
  <Button type="submit" loading={isSubmitting}>Save</Button>
</Form>
```

### Notifications

- Toast notifications for success/error
- Real-time updates via polling or WebSocket

---

## 📋 API Response Patterns

### Paginated Lists

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "size": 20
}
```

### Standard Success

```json
{
  "success": true,
  "message": "Operation completed"
}
```

### Error Response

```json
{
  "detail": {
    "code": "VALIDATION_ERROR",
    "message": "Email already exists",
    "status_code": 400
  }
}
```

---

## 🔧 Key Features to Implement

### 1. Multi-Step Registration Flow

`POST /tenants/register` → Creates school + admin user + starts trial

### 2. Permission-Based UI

```tsx
// Hide/show based on permissions
{
  hasPermission("user:create") && <CreateUserButton />;
}
{
  hasAnyRole(["teacher", "principal"]) && <GradingModule />;
}
```

### 3. Data Refresh Patterns

- Auto-refresh attendance on interval
- Invalidate queries on mutations
- Optimistic updates for better UX

### 4. File Upload

- Profile pictures
- Document uploads (assignments, applications)
- Use `/files` endpoints

### 5. Export Features

- Export reports as PDF/Excel
- Print-friendly views for hall tickets, receipts

---

## 🔑 RBAC Permission Reference

Key permissions (90+ total):

```
user:view, user:create, user:update, user:delete, user:manage_roles
student:view, student:create, student:update, student:lifecycle_manage
teacher:view, teacher:create
class:view, class:create, class:update
attendance:view, attendance:mark, attendance:report
fee:view, fee:component_manage, fee:structure_manage, fee:invoice_generate
survey:view, survey:create, survey:results_view, survey:submit
analytics:view_admin, analytics:view_teacher, analytics:view_student
```

---

## 📱 Page Priority (Build Order)

### Phase 1: Core

1. Login/Auth flow with tenant branding
2. Dashboard shells for each role
3. User management (CRUD)
4. Academic structure setup

### Phase 2: Operations

5. Attendance marking and views
6. Timetable management
7. Announcements/circulars

### Phase 3: Finance

8. Fee configuration
9. Invoice generation
10. Payment integration

### Phase 4: Advanced

11. Examinations flow
12. Analytics dashboards
13. Feedback/surveys
14. Helpdesk

### Phase 5: Polish

15. AI features integration
16. Reports and exports
17. Mobile optimization
18. Real-time notifications

---

## 🛠️ Development Notes

### Environment Variables

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_APP_NAME=CUSTOS
```

### Error Handling

Wrap API calls with try-catch, handle:

- 401 → Redirect to login
- 403 → Show permission denied
- 404 → Show not found
- 500 → Show generic error

### Testing Credentials

```
Platform Admin: admin@custos.school / Admin@123
Test Tenant Slug: demo-school
```

---

## 📖 Quick Start Steps

1. Create Next.js project with TypeScript
2. Install shadcn/ui, configure Tailwind
3. Set up auth context with token refresh
4. Build login page with tenant lookup
5. Create role-based layout wrapper
6. Implement dashboard for each role
7. Add modules incrementally following Phase order

---

**Backend Docs**: OpenAPI schema at `http://localhost:8000/docs`
