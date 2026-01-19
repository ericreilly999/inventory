# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${var.environment}-inventory-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [var.security_group_id]
  subnets            = var.public_subnet_ids

  enable_deletion_protection = var.enable_deletion_protection

  tags = merge(var.tags, {
    Name = "${var.environment}-inventory-alb"
  })
}

# Target Group for API Gateway
resource "aws_lb_target_group" "api_gateway" {
  name     = "${var.environment}-inventory-api-tg"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = var.vpc_id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  target_type = "ip"

  tags = merge(var.tags, {
    Name = "${var.environment}-inventory-api-tg"
  })
}

# Target Group for UI Service
resource "aws_lb_target_group" "ui" {
  name     = "${var.environment}-inventory-ui-tg"
  port     = 80
  protocol = "HTTP"
  vpc_id   = var.vpc_id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  target_type = "ip"

  tags = merge(var.tags, {
    Name = "${var.environment}-inventory-ui-tg"
  })
}

# HTTP Listener for development (when no certificate)
resource "aws_lb_listener" "http_dev" {
  count = var.certificate_arn == null ? 1 : 0

  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.ui.arn
  }

  tags = merge(var.tags, {
    Name = "${var.environment}-inventory-http-dev-listener"
  })
}

# Listener Rule for API Gateway
resource "aws_lb_listener_rule" "api_gateway" {
  listener_arn = aws_lb_listener.http_dev[0].arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api_gateway.arn
  }

  condition {
    path_pattern {
      values = ["/api/*"]
    }
  }

  tags = merge(var.tags, {
    Name = "${var.environment}-inventory-api-rule"
  })
}