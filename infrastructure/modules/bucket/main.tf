resource "aws_s3_bucket" "this" {
  bucket = var.name
  tags = {
    Name = var.name
  }
}

resource "aws_s3_bucket_ownership_controls" "this" {
  bucket = aws_s3_bucket.this.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
  # Add just this depends_on condition
  depends_on = [aws_s3_bucket_acl.this]
}

resource "aws_s3_bucket_acl" "this" {
  bucket = aws_s3_bucket.this.id
  acl    = "private"
}