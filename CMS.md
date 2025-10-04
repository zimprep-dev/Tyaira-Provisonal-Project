# Driving Test CMS - System Architecture & Requirements

## Overview
A comprehensive Content Management System for creating and managing driving theory tests with image-based questions, particularly focused on "give way" scenarios where users identify which vehicle should yield in traffic diagrams.

## Core Features

### 1. Test Content Management
- **Question Creation**: Create questions with both text and image components
- **Image Upload**: Support for traffic diagram images (PNG, JPG, JPEG, WebP)
- **Multiple Choice Answers**: Configure 2-4 answer options per question
- **Question Categories**: Organize by test type (give way, road signs, rules, etc.)
- **Question Bank**: Maintain large pool of questions for random selection

### 2. Test Configuration
- **Test Sets**: Create predefined test configurations
- **Question Limits**: Set number of questions per test (default: 25)
- **Time Limits**: Configurable timer per test (e.g., 30 minutes)
- **Random Selection**: Randomly select questions from categories
- **Difficulty Levels**: Basic, Intermediate, Advanced question classification

### 3. File Management
- **Image Storage**: Secure storage for question diagrams
- **PDF Resources**: Upload downloadable study materials
- **File Organization**: Categorized file structure
- **CDN Integration**: Fast image delivery for production

### 4. User Test Experience
- **Test Sessions**: Track individual test attempts
- **Progress Tracking**: Save/resume test capability
- **Timer Display**: Real-time countdown
- **Image Zoom**: Allow users to examine diagrams closely
- **Results & Scoring**: Immediate feedback and detailed results

## Technical Architecture

### Backend Stack
- **Framework**: Flask (Python) - Current codebase foundation
- **Database**: SQLite (development) → PostgreSQL (production)
- **File Storage**: Local storage (dev) → AWS S3/DigitalOcean Spaces (prod)
- **Authentication**: Flask-Login for admin access
- **API**: RESTful endpoints for frontend communication

### Frontend Stack
- **Templates**: Jinja2 with responsive HTML/CSS
- **JavaScript**: Vanilla JS for interactivity
- **UI Framework**: Bootstrap 5 for responsive design
- **Image Handling**: Progressive loading and zoom functionality

### Database Schema

#### Tables Structure
```sql
-- Test Categories
tests_categories (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP
)

-- Questions
questions (
    id INTEGER PRIMARY KEY,
    category_id INTEGER REFERENCES tests_categories(id),
    question_text TEXT NOT NULL,
    image_path VARCHAR(255),
    difficulty_level ENUM('basic', 'intermediate', 'advanced'),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)

-- Answer Options
answer_options (
    id INTEGER PRIMARY KEY,
    question_id INTEGER REFERENCES questions(id),
    option_text VARCHAR(255) NOT NULL,
    is_correct BOOLEAN DEFAULT FALSE,
    option_order INTEGER
)

-- Test Configurations
test_configs (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    question_count INTEGER DEFAULT 25,
    time_limit_minutes INTEGER DEFAULT 30,
    category_ids JSON, -- Array of category IDs to include
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP
)

-- Test Sessions
test_sessions (
    id INTEGER PRIMARY KEY,
    user_id VARCHAR(100), -- Can be anonymous session ID
    test_config_id INTEGER REFERENCES test_configs(id),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    score INTEGER,
    total_questions INTEGER,
    status ENUM('in_progress', 'completed', 'expired'),
    session_data JSON -- Store answers and progress
)

-- Downloadable Resources
resources (
    id INTEGER PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    file_type ENUM('pdf', 'image', 'document'),
    category VARCHAR(100),
    description TEXT,
    download_count INTEGER DEFAULT 0,
    created_at TIMESTAMP
)
```

## CMS Admin Interface

### Dashboard Features
- **Statistics Overview**: Total questions, active tests, user sessions
- **Quick Actions**: Add question, create test, upload resources
- **Recent Activity**: Latest questions added, test sessions completed

### Question Management
- **Question List**: Paginated view with search and filters
- **Question Editor**: Rich text editor with image upload
- **Bulk Operations**: Import/export questions, batch category assignment
- **Preview Mode**: Test question display before publishing

### Test Configuration
- **Test Builder**: Drag-and-drop interface for creating test sets
- **Category Selection**: Choose which question categories to include
- **Settings Panel**: Configure time limits, question counts, difficulty mix
- **Test Preview**: Sample test generation for validation

### File Management
- **Image Gallery**: Visual browser for uploaded diagrams
- **PDF Library**: Manage downloadable study materials
- **Storage Analytics**: File usage and storage statistics
- **Bulk Upload**: Multiple file upload with progress tracking

## User-Facing Features

### Test Taking Interface
- **Clean UI**: Minimal distractions during test
- **Image Viewer**: Zoomable diagrams with pan functionality
- **Progress Bar**: Visual indication of test completion
- **Timer Display**: Countdown with warnings at 5 and 1 minute remaining
- **Navigation**: Previous/Next question with review capability

### Results & Analytics
- **Immediate Scoring**: Show results upon completion
- **Detailed Breakdown**: Performance by category and difficulty
- **Correct Answers**: Review mode showing right/wrong answers
- **Performance History**: Track improvement over multiple attempts

## Production Deployment Strategy

### Cloud Platform Options

#### AWS Deployment
- **Compute**: EC2 instances or Elastic Beanstalk
- **Database**: RDS PostgreSQL with automated backups
- **Storage**: S3 for images/PDFs with CloudFront CDN
- **Load Balancing**: Application Load Balancer for high availability
- **Monitoring**: CloudWatch for performance metrics

#### DigitalOcean Deployment
- **Compute**: Droplets with managed databases
- **Database**: Managed PostgreSQL cluster
- **Storage**: Spaces for file storage with CDN
- **Load Balancing**: Load Balancer service
- **Monitoring**: Built-in monitoring dashboard

#### Google Cloud Platform
- **Compute**: App Engine or Compute Engine
- **Database**: Cloud SQL PostgreSQL
- **Storage**: Cloud Storage with CDN
- **Load Balancing**: Cloud Load Balancing
- **Monitoring**: Cloud Monitoring

### Deployment Configuration
- **Environment Variables**: Database URLs, API keys, storage credentials
- **SSL/TLS**: HTTPS enforcement with Let's Encrypt certificates
- **Domain Management**: Custom domain with DNS configuration
- **Backup Strategy**: Automated database and file backups
- **Scaling**: Auto-scaling based on traffic patterns

## Security Considerations
- **Admin Authentication**: Secure login for CMS access
- **File Validation**: Image and PDF upload security checks
- **SQL Injection Protection**: Parameterized queries
- **CSRF Protection**: Token-based form security
- **Rate Limiting**: Prevent abuse of test-taking endpoints
- **Data Privacy**: GDPR compliance for user data handling

## Development Phases

### Phase 1: Core CMS (Week 1-2)
- Basic question CRUD operations
- Image upload functionality
- Simple test configuration
- Admin authentication

### Phase 2: Test Engine (Week 3-4)
- Test session management
- Timer functionality
- Question randomization
- Results calculation

### Phase 3: Enhanced Features (Week 5-6)
- PDF resource management
- Advanced test configuration
- User analytics
- Performance optimization

### Phase 4: Production Deployment (Week 7-8)
- Cloud platform setup
- Database migration
- CDN configuration
- Performance testing

## Technical Requirements

### Performance Targets
- **Page Load Time**: < 2 seconds for question pages
- **Image Load Time**: < 1 second for diagrams
- **Concurrent Users**: Support 100+ simultaneous test takers
- **Database Response**: < 100ms for question queries

### Browser Compatibility
- **Modern Browsers**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Mobile Support**: Responsive design for tablets and phones
- **Accessibility**: WCAG 2.1 AA compliance

### Storage Requirements
- **Images**: Optimized formats, max 2MB per image
- **PDFs**: Max 10MB per document
- **Database**: Estimated 1GB for 10,000 questions
- **Backup**: Daily automated backups with 30-day retention

## Next Steps for Discussion
1. **Question Format Standardization**: Define exact structure for give-way questions
2. **User Authentication**: Decide on anonymous vs. registered user approach
3. **Scoring Algorithm**: Define how partial credit and time bonuses work
4. **Content Migration**: Plan for importing existing question banks
5. **Integration Requirements**: APIs for external systems or mobile apps