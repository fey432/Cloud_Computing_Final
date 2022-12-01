# AWS Serverless OCR and Word Count Function
### Authors: Raymond Fey, Haibo Chu, Jie Xu

### Team: Hard Coders

# Description
In this project, we created a server-less function to allow users to upload a text-filled image to a storage bucket and the word count will be provided. The picture will be processed using Optical Character Recognition (OCR) and the word count through PySpark.

# How to Use

[Access Here](http://hardcoders-front-end.s3-website-us-east-1.amazonaws.com)

If the link does not work, please copy this link in your browser http://hardcoders-front-end.s3-website-us-east-1.amazonaws.com

1. Verify your email with Amazon Web Services (AWS) Simple Email Service (SES) before uploading any image.
    1. To verify, navigate to the bottom card which states `Amazon Simple Email Service (SES) Verification`
    2. Type in your email address and click on `Verify`
    3. You should see an email shortly, and follow the steps as written in the email.
2. Now you can use the service
    1. On the top card which states `Image Picker`, you can type in your email and select an image.
    2. To select an image, click on `Select An Image`.
    3. A dialogue window should show up, and click on `Choose File`
    4. Choose the file and click `Ok`
    5. Click on `Upload`
    6. Depending on the image is new or not, the email may take up to 5 minutes to receive.
    7. If you receive an email saying that there was error trying to get your results, please try the upload again.

**NOTE:** As of 11/30/2022, there is currently an issue with S3 Buckets and Trigger Events with Lambda. `.TIFF` file formats currently do not trigger.