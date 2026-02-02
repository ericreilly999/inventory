terraform {
  backend "s3" {
    bucket         = "inventory-terraform-state"
    key            = "staging/terraform.tfstate"
    region         = "us-west-2"
    dynamodb_table = "terraform-state-lock"
    encrypt        = true
  }
}
