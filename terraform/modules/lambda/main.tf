data aws_caller_identity current {}

locals {
  account_id = data.aws_caller_identity.current.account_id
  parent     = "${path.root}/.."
}

resource aws_ecr_repository lambda {
  name = var.name
}

resource null_resource lambda {
  triggers = {
    flows_sha1 = sha1(join("", [for f in fileset("${local.parent}/flows/", "**/*"): filesha1("${local.parent}/flows/${f}")]))
    packages_sha1 = sha1(join("", [for f in fileset("${local.parent}/packages/", "**/*"): filesha1("${local.parent}/packages/${f}")]))
    shared_sha1 = sha1(join("", [for f in fileset("${local.parent}/shared/", "**/*"): filesha1("${local.parent}/shared/${f}")]))

    python_file  = md5(file("${local.parent}/${var.folder}/lambda.py"))
    docker_file  = md5(file("${local.parent}/${var.folder}/Dockerfile"))
    requirements = md5(file("${local.parent}/lambda/requirements.txt"))
  }

  provisioner "local-exec" {
    command = <<EOF
           aws ecr get-login-password --region ${var.region} | docker login --username AWS --password-stdin ${local.account_id}.dkr.ecr.${var.region}.amazonaws.com
           docker build --build-arg ENV=${var.env} --build-arg PROJECT=${var.project} -t ${aws_ecr_repository.lambda.repository_url}:${var.tag} -f ${local.parent}/${var.folder}/Dockerfile ${local.parent}
           docker push ${aws_ecr_repository.lambda.repository_url}:${var.tag}
       EOF
  }
}

data aws_ecr_image lambda {
  depends_on = [
    null_resource.lambda
  ]
  repository_name = aws_ecr_repository.lambda.name
  image_tag       = var.tag
}

resource aws_lambda_function lambda {
  depends_on = [
    null_resource.lambda
  ]
  function_name = var.name
  role          = var.lambda_role_arn
  timeout       = 300
  image_uri     = "${aws_ecr_repository.lambda.repository_url}@${data.aws_ecr_image.lambda.id}"
  package_type  = "Image"
  architectures = [var.architecture]
}
