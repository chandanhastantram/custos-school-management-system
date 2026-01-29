# CUSTOS - AI-Powered School Management System

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-teal)
![License](https://img.shields.io/badge/license-MIT-orange)

## 🎯 Overview

CUSTOS is a comprehensive, AI-powered school management SaaS platform designed for educational institutions. It features multi-tenant architecture, role-based access control, and intelligent automation for academic workflows.

## ✨ Features

### 🏫 Multi-Tenant Architecture
- Complete data isolation per school/institution
- Custom branding per tenant
- Flexible subscription plans

### 👥 Role-Based Access Control
- **Super Admin** - Full system access
- **Principal** - School-wide management
- **Sub Admin** - Administrative tasks
- **Teacher** - Academic content & grading
- **Student** - Learning & submissions
- **Parent** - Monitoring child's progress

### 📚 Academic Management
- Academic years, classes, sections
- Subject catalog with teacher assignments
- Syllabus management with topic hierarchy
- Lesson planning (manual + AI-generated)

### ❓ Question Bank Engine
- Multiple question types (MCQ, True/False, Short Answer, etc.)
- Bloom's Taxonomy classification
- Difficulty levels (Easy, Medium, Hard, Expert)
- AI-powered question generation
- Review workflow for quality control

### 📝 Assignments & Worksheets
- Create assignments with question selection
- AI-generated worksheets
- Time-limited assessments
- Auto-grading for objective questions
- Manual correction workflow

### ✅ Manual Correction Workflow
- Spreadsheet-style grading interface
- Bulk correction support
- Per-question feedback
- Performance tracking

### 🤖 AI Features
- **Lesson Plan Generator** - Create comprehensive lesson plans from syllabus
- **Question Generator** - Generate MCQs and questions by topic/difficulty
- **Doubt Solver** - AI tutor for student questions
- **OCR Engine** - Process exam answer sheets
- **Per-plan quotas** - Different limits by subscription tier
- Usage tracking per tenant

### 📊 Analytics & Reports
- Student performance reports
- Class analytics
- Teacher effectiveness metrics
- Custom report generation

### 💳 SaaS Billing
- Multiple subscription tiers
- Feature-based access control
- Usage limits enforcement
- Trial periods

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with SQLAlchemy (async)
- **Authentication**: JWT with bcrypt
- **AI**: OpenAI GPT-4
- **Task Queue**: Redis Queue (RQ) for background jobs
- **Matching**: Fuzzy matching for OCR identifiers
- **Migrations**: Alembic

## 📦 Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- OpenAI API key

### Setup

1. **Clone the repository**
```bash
cd custos
```

2. **Create virtual environment**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
copy .env.example .env
# Edit .env with your settings
```

5. **Create database**
```bash
# In PostgreSQL
CREATE DATABASE custos_db;
```

6. **Run migrations**
```bash
alembic upgrade head
```

7. **Seed initial data**
```bash
python scripts/seed.py
```

8. **Start the server**
```bash
uvicorn app.main:app --reload
```

## 🔑 Default Credentials

After seeding, use these credentials for the demo school:

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@demo-school.edu | Admin@123 |
| Teacher | teacher@demo-school.edu | Teacher@123 |
| Student | student@demo-school.edu | Student@123 |

## 📚 API Documentation

Once running, access the interactive API docs:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🗂️ Project Structure

```
custos/
├── app/
│   ├── ai/              # AI integrations
│   ├── api/             # API endpoints
│   │   └── v1/          # Version 1 routes
│   ├── auth/            # Authentication & RBAC
│   ├── core/            # Core configurations
│   ├── models/          # SQLAlchemy models
│   ├── repositories/    # Data access layer
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   └── main.py          # FastAPI app
├── alembic/             # Database migrations
├── scripts/             # Utility scripts
├── tests/               # Test suite
├── requirements.txt     # Dependencies
└── .env.example         # Environment template
```

## 🔒 Security Features

- JWT-based authentication
- Password hashing with bcrypt
- Role-based access control (RBAC)
- Tenant data isolation
- Rate limiting (configurable)
- CORS protection

## 📊 Database Schema

Key entities:
- **Tenant** - School/Institution
- **User** - All user types with profiles
- **Class/Section** - Academic structure
- **Subject/Syllabus/Topic** - Curriculum
- **Question** - Question bank
- **Assignment/Submission** - Work management
- **Report** - Analytics data

## 🚀 Deployment

### Docker (Recommended)
```bash
docker-compose up -d
```

### Railway/Render
1. Connect your repository
2. Set environment variables
3. Deploy

## 📈 Roadmap

- [ ] Mobile app (React Native)
- [ ] Parent portal
- [ ] Attendance management
- [ ] Fee management
- [ ] Library management
- [ ] Transport tracking
- [ ] WhatsApp integration
- [ ] Video conferencing

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open a Pull Request

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 💬 Support

- 📧 Email: support@custos.app
- 📖 Documentation: https://docs.custos.app
- 💬 Discord: https://discord.gg/custos

---

Built with ❤️ for educators worldwide
