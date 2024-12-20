
Jewelry Scraper - Cloud Deployment Plan
1. Infrastructure as Code (IaC)
1.1 AWS Infrastructure (terraform/main.tf)
hcl
Copy code
provider "aws" {
  region = "us-west-2"
}

# VPC Configuration
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  
  name = "jewelry-scraper-vpc"
  cidr = "10.0.0.0/16"
  
  azs             = ["us-west-2a", "us-west-2b"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]
  
  enable_nat_gateway = true
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "jewelry-scraper-cluster"
  
  capacity_providers = ["FARGATE", "FARGATE_SPOT"]
  
  default_capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight           = 1
  }
}
1.2 Container Definition (Dockerfile)
dockerfile
Copy code
# Backend API
FROM python:3.10-slim

# Install Chrome and dependencies
RUN apt-get update && apt-get install -y \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["gunicorn", "--workers=4", "--bind=0.0.0.0:8000", "app:app"]

# Frontend
FROM node:16-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
2. Database Migration
2.1 RDS Setup (terraform/database.tf)
hcl
Copy code
resource "aws_db_instance" "main" {
  identifier        = "jewelry-scraper-db"
  engine           = "postgresql"
  engine_version   = "13.7"
  instance_class   = "db.t3.medium"
  allocated_storage = 20
  
  name     = "jewelry_scraper"
  username = var.db_username
  password = var.db_password
  
  backup_retention_period = 7
  multi_az               = true
  skip_final_snapshot    = false
  
  vpc_security_group_ids = [aws_security_group.db.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
}
2.2 Data Migration Script
python
Copy code
from sqlalchemy import create_engine
import pandas as pd

class DatabaseMigrator:
    def __init__(self, source_url: str, target_url: str):
        self.source = create_engine(source_url)
        self.target = create_engine(target_url)
    
    async def migrate(self):
        # Migrate in batches
        batch_size = 1000
        offset = 0
        
        while True:
            query = f"""
                SELECT * FROM products 
                ORDER BY id 
                LIMIT {batch_size} 
                OFFSET {offset}
            """
            
            df = pd.read_sql(query, self.source)
            if df.empty:
                break
                
            df.to_sql('products', self.target, 
                     if_exists='append', index=False)
            offset += batch_size
3. Image Storage Solution
3.1 S3 Configuration (terraform/storage.tf)
hcl
Copy code
resource "aws_s3_bucket" "images" {
  bucket = "jewelry-scraper-images"
}

resource "aws_s3_bucket_policy" "images" {
  bucket = aws_s3_bucket.images.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.ecs_task_role.arn
        }
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.images.arn}/*"
      }
    ]
  })
}
3.2 Image Processing Pipeline
python
Copy code
class CloudImageProcessor:
    def __init__(self):
        self.s3 = boto3.client('s3')
        self.bucket = "jewelry-scraper-images"
    
    async def process_and_upload(self, image_url: str) -> str:
        # Download image
        image_data = await self.download_image(image_url)
        
        # Process image
        processed = await self.optimize_image(image_data)
        
        # Generate unique path
        path = f"products/{uuid.uuid4()}.jpg"
        
        # Upload to S3
        await self.upload_to_s3(processed, path)
        
        return f"https://{self.bucket}.s3.amazonaws.com/{path}"
4. Scaling Configuration
4.1 Auto Scaling (terraform/scaling.tf)
hcl
Copy code
resource "aws_appautoscaling_target" "ecs_target" {
  max_capacity       = 10
  min_capacity       = 1
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.main.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "ecs_policy" {
  name               = "scale-based-on-cpu"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 70.0
  }
}
4.2 Load Balancer Configuration
hcl
Copy code
resource "aws_lb" "main" {
  name               = "jewelry-scraper-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = module.vpc.public_subnets
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.main.arn
  }
}
5. Monitoring & Logging
5.1 CloudWatch Configuration
python
Copy code
class CloudMonitor:
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch')
    
    async def log_metrics(self, metrics: dict):
        timestamp = datetime.utcnow()
        
        for name, value in metrics.items():
            await self.cloudwatch.put_metric_data(
                Namespace='JewelryScraper',
                MetricData=[{
                    'MetricName': name,
                    'Value': value,
                    'Timestamp': timestamp,
                    'Unit': 'Count'
                }]
            )
5.2 Alerts Configuration
hcl
Copy code
resource "aws_cloudwatch_metric_alarm" "scraping_errors" {
  alarm_name          = "scraping-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ScrapingErrors"
  namespace           = "JewelryScraper"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "This metric monitors scraping errors"
  alarm_actions       = [aws_sns_topic.alerts.arn]
}
6. Security Configuration
6.1 IAM Roles
hcl
Copy code
resource "aws_iam_role" "ecs_task_role" {
  name = "jewelry-scraper-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}
6.2 Security Groups
hcl
Copy code
resource "aws_security_group" "ecs_tasks" {
  name        = "jewelry-scraper-ecs-tasks"
  description = "Allow inbound traffic for ECS tasks"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
7. Deployment Pipeline
7.1 GitHub Actions Workflow (.github/workflows/deploy.yml)
yaml
Copy code
name: Deploy to AWS

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-west-2
      
      - name: Build and push Docker images
        run: |
          docker build -t jewelry-scraper-api ./backend
          docker build -t jewelry-scraper-frontend ./frontend
          aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.us-west-2.amazonaws.com
          docker tag jewelry-scraper-api:latest ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.us-west-2.amazonaws.com/jewelry-scraper-api:latest
          docker tag jewelry-scraper-frontend:latest ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.us-west-2.amazonaws.com/jewelry-scraper-frontend:latest
          docker push ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.us-west-2.amazonaws.com/jewelry-scraper-api:latest
          docker push ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.us-west-2.amazonaws.com/jewelry-scraper-frontend:latest
      
      - name: Deploy to ECS
        run: |
          aws ecs update-service --cluster jewelry-scraper-cluster --service jewelry-scraper-service --force-new-deployment
8. Cost Optimization
8.1 Resource Scheduling
python
Copy code
class ResourceScheduler:
    def __init__(self):
        self.ecs = boto3.client('ecs')
    
    async def scale_based_on_demand(self):
        # Scale down during off-hours
        current_hour = datetime.utcnow().hour
        if 2 <= current_hour <= 6:  # UTC time
            await self.ecs.update_service(
                cluster='jewelry-scraper-cluster',
                service='jewelry-scraper-service',
                desiredCount=1
            )
End of Cloud Deployment Plan Documentation 
