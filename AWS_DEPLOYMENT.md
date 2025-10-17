# AWS Ubuntu Deployment Guide for Tyaira

Complete guide to deploy the Tyaira Driver Testing Platform on AWS EC2 Ubuntu.

## 📋 Prerequisites

- AWS Account with EC2 access
- Domain name (optional but recommended)
- SSH client installed
- GitHub repository access

## 🚀 Quick Start (30-minute setup)

### Step 1: Launch EC2 Instance

1. **AWS Console** → EC2 → Launch Instance
2. **Configuration:**
   - **Name:** tyaira-production
   - **OS:** Ubuntu Server 22.04 LTS
   - **Instance Type:** t2.small (recommended) or t2.micro (free tier)
   - **Key Pair:** Create/select SSH key pair (download .pem file)
   - **Security Group:** Create with these rules:
     - SSH (22) - Your IP only
     - HTTP (80) - Anywhere (0.0.0.0/0)
     - HTTPS (443) - Anywhere (0.0.0.0/0)
   - **Storage:** 30 GB General Purpose SSD

3. **Launch Instance**

4. **Optional:** Allocate Elastic IP
   - EC2 → Elastic IPs → Allocate
   - Associate with your instance

### Step 2: Connect to Server

```bash
# Windows PowerShell or Mac/Linux Terminal
chmod 400 your-key.pem  # Mac/Linux only
ssh -i your-key.pem ubuntu@your-ec2-ip
```

### Step 3: Install System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Install PostgreSQL (if using local database)
sudo apt install -y postgresql postgresql-contrib

# Install Nginx
sudo apt install -y nginx

# Install Git and build tools
sudo apt install -y git build-essential libpq-dev

# Install Certbot for SSL (optional, for HTTPS)
sudo apt install -y certbot python3-certbot-nginx
```

### Step 4: Setup Database

**Option A: Local PostgreSQL on EC2**

```bash
# Create database and user
sudo -u postgres psql <<EOF
CREATE DATABASE tyaira;
CREATE USER tyaira_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE tyaira TO tyaira_user;
ALTER DATABASE tyaira OWNER TO tyaira_user;
\q
EOF

# Your DATABASE_URL:
# postgresql://tyaira_user:your_secure_password@localhost/tyaira
```

**Option B: AWS RDS PostgreSQL (Recommended)**

1. AWS Console → RDS → Create Database
2. Choose PostgreSQL, version 15.x
3. Template: Free tier or Production
4. Settings:
   - DB instance: tyaira
   - Master username: postgres
   - Master password: [strong password]
5. Connectivity: Same VPC as EC2
6. Security: Create security group, allow port 5432 from EC2
7. Copy endpoint: `tyaira.abc123.us-east-1.rds.amazonaws.com`

```bash
# Your DATABASE_URL:
# postgresql://postgres:password@tyaira.abc123.us-east-1.rds.amazonaws.com:5432/tyaira
```

### Step 5: Clone and Setup Application

```bash
# Clone repository
cd /home/ubuntu
git clone https://github.com/zimprep-dev/Tyaira-Provisonal-Project.git
cd Tyaira-Provisonal-Project

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 6: Configure Environment Variables

```bash
# Copy example and edit
cp .env.example .env
nano .env
```

**Required environment variables:**

```bash
# MUST CHANGE THESE:
SECRET_KEY=generate-a-random-secret-key-here
DATABASE_URL=your-database-url-from-step-4
BASE_URL=https://yourdomain.com  # or http://your-ec2-ip

# Paynow credentials (already configured):
PAYNOW_INTEGRATION_ID=22233
PAYNOW_INTEGRATION_KEY=5edbeab4-3c75-4132-9785-a81b3fde4bde

# Admin (change as needed):
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_USERNAME=admin
```

**Generate SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 7: Initialize Database

```bash
# Activate virtual environment if not already active
source venv/bin/activate

# Run migrations
flask db upgrade

# Create admin user (follow prompts)
python create_admin.py

# Initialize subscription plans
python init_subscription_plans.py

# Import questions
python import_if_empty.py
```

### Step 8: Setup Systemd Service

```bash
# Create log directory
sudo mkdir -p /var/log/tyaira
sudo chown ubuntu:www-data /var/log/tyaira

# Copy service file
sudo cp tyaira.service /etc/systemd/system/

# Reload systemd and start service
sudo systemctl daemon-reload
sudo systemctl enable tyaira
sudo systemctl start tyaira

# Check status
sudo systemctl status tyaira
```

### Step 9: Configure Nginx

```bash
# Update nginx.conf with your domain/IP
nano nginx.conf
# Change: server_name yourdomain.com www.yourdomain.com;
# Or: server_name 54.123.45.67;  (your EC2 IP)

# Copy to nginx sites
sudo cp nginx.conf /etc/nginx/sites-available/tyaira
sudo ln -s /etc/nginx/sites-available/tyaira /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### Step 10: Setup Firewall (UFW)

```bash
# Configure firewall
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

### Step 11: Setup SSL/HTTPS (Optional but Recommended)

**Only if you have a domain name:**

```bash
# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Follow prompts:
# - Enter email
# - Agree to terms
# - Choose: Redirect HTTP to HTTPS (option 2)

# Certbot auto-configures Nginx and sets up auto-renewal
```

**Verify auto-renewal:**
```bash
sudo certbot renew --dry-run
```

## ✅ Verification

### Check Services

```bash
# Check application service
sudo systemctl status tyaira

# Check Nginx
sudo systemctl status nginx

# Check logs
sudo journalctl -u tyaira -f  # Application logs
sudo tail -f /var/log/nginx/tyaira_error.log  # Nginx logs
```

### Test Application

```bash
# From your local machine:
curl http://your-ec2-ip
# Or visit in browser: http://your-ec2-ip
```

## 🔄 Deploying Updates

### Method 1: Use deploy.sh script

```bash
# Make script executable (first time only)
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

### Method 2: Manual deployment

```bash
cd /home/ubuntu/Tyaira-Provisonal-Project
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
flask db upgrade
sudo systemctl restart tyaira
```

## 📊 Monitoring & Maintenance

### View Logs

```bash
# Application logs (real-time)
sudo journalctl -u tyaira -f

# Application logs (last 100 lines)
sudo journalctl -u tyaira -n 100

# Nginx access logs
sudo tail -f /var/log/nginx/tyaira_access.log

# Nginx error logs
sudo tail -f /var/log/nginx/tyaira_error.log
```

### Common Commands

```bash
# Restart application
sudo systemctl restart tyaira

# Restart Nginx
sudo systemctl restart nginx

# Check service status
sudo systemctl status tyaira
sudo systemctl status nginx

# Test Nginx configuration
sudo nginx -t

# Reload Nginx (without downtime)
sudo systemctl reload nginx
```

### Database Backup

```bash
# Create backup
pg_dump -U tyaira_user -h localhost tyaira > backup_$(date +%Y%m%d).sql

# Restore backup
psql -U tyaira_user -h localhost tyaira < backup_20251017.sql
```

## 🔧 Troubleshooting

### Application won't start

```bash
# Check logs
sudo journalctl -u tyaira -n 50

# Check if port is in use
sudo lsof -i :8000

# Verify environment variables
cat .env

# Test application manually
source venv/bin/activate
gunicorn wsgi:app
```

### Nginx errors

```bash
# Test configuration
sudo nginx -t

# Check error logs
sudo tail -f /var/log/nginx/error.log

# Verify socket file exists
ls -la /home/ubuntu/Tyaira-Provisonal-Project/tyaira.sock
```

### Database connection errors

```bash
# Test PostgreSQL connection
psql -U tyaira_user -h localhost tyaira

# Check if PostgreSQL is running
sudo systemctl status postgresql

# Verify DATABASE_URL in .env
grep DATABASE_URL .env
```

### Permission errors

```bash
# Fix ownership
sudo chown -R ubuntu:www-data /home/ubuntu/Tyaira-Provisonal-Project

# Fix socket permissions
sudo chmod 660 /home/ubuntu/Tyaira-Provisonal-Project/tyaira.sock
```

## 🔐 Security Best Practices

1. **Never commit `.env` file** - Contains secrets
2. **Use strong passwords** - Database, admin account
3. **Keep system updated** - `sudo apt update && sudo apt upgrade`
4. **Use SSH keys only** - Disable password authentication
5. **Configure firewall** - Only open necessary ports
6. **Enable HTTPS** - Use Let's Encrypt SSL
7. **Regular backups** - Database and uploaded files
8. **Monitor logs** - Check for suspicious activity

## 💰 Cost Estimate

| Service | Monthly Cost |
|---------|--------------|
| EC2 t2.small | ~$17 |
| 30GB EBS Storage | ~$3 |
| Elastic IP | Free (if attached) |
| Data Transfer | ~$1-5 (typical) |
| **Total** | **~$21-25/month** |

**Free Tier:** If eligible, t2.micro is free for 12 months

## 📞 Support

- Application issues: Check GitHub repository
- AWS issues: AWS Support Center
- Paynow issues: Paynow support

## 📝 Post-Deployment Checklist

- [ ] Application accessible via browser
- [ ] Admin account created and working
- [ ] Payment integration tested
- [ ] SSL certificate installed (if using domain)
- [ ] Database backups configured
- [ ] Monitoring setup complete
- [ ] deploy.sh script tested
- [ ] Logs rotating properly
- [ ] Firewall configured
- [ ] DNS configured (if using domain)

---

**🎉 Congratulations! Your Tyaira platform is now live on AWS!**
