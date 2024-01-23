docker build --pull --rm -f "Dockerfile" -t loans:latest "."
docker tag loans:latest cr.yandex/crp8ek2lo6uuvnveblac/loans
docker push cr.yandex/crp8ek2lo6uuvnveblac/loans
yc serverless container revision deploy --container-name loans --image cr.yandex/crp8ek2lo6uuvnveblac/loans --cores 1 --memory 256MB --concurrency 1 --execution-timeout 10s --service-account-id ajeeqpdslsj7pt0usup8
