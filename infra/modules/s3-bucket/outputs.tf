output "bucket_name" {
  description = "The name of the bucket that was created"
  value       = aws_s3_bucket.this.bucket
}
