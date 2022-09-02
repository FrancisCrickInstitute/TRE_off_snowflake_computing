FROM public.ecr.aws/lambda/python:3.8

ARG PROJECT
ARG ENV

ENV project=$PROJECT
ENV env=$ENV

# Install development tools
RUN yum -y groupinstall "Development Tools"

# Install the function's dependencies using file requirements.txt
COPY lambda/requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy flows and packages
COPY flows ${LAMBDA_TASK_ROOT}/flows
COPY packages ${LAMBDA_TASK_ROOT}/packages
COPY shared ${LAMBDA_TASK_ROOT}/shared

# Copy function specific files
COPY lambda/create_account/lambda.py ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "lambda.handler" ]