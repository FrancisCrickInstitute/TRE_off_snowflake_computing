data "template_file" "template" {
  template = file(var.template)

  vars = {
    project = var.project
  }
}

resource "aws_iam_policy" "policy" {
  name = "policy-${var.project}-${var.name}"
  policy = data.template_file.template.rendered
}

resource "aws_iam_group" "group" {
  name = "group-${var.project}-${var.name}"
  depends_on = [aws_iam_policy.policy]
}

resource "aws_iam_group_policy_attachment" "group-attachment" {
  group      = aws_iam_group.group.name
  policy_arn = aws_iam_policy.policy.arn
  depends_on = [aws_iam_group.group, aws_iam_policy.policy]
}

