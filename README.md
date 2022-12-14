# covidimaging environment

This is a FHIR-first platform which stores all information as first-rate FHIR resources, embracing FOSS paradigm. We used the AidBox platform as a FOSS solution to provide this base FHIR functionality and to satisfy HIPAA safeguards and security. We extended AidBox to capture patient imaging as DICOM files in FHIR when they were available. We allowed for appropriate API access to the data collected to serve patients and study coordinators the questionnaires appropriately. For
questionnaires such is ICHOM, the system utilizes FHIR SDC (structured data capturing) approach to deal with any kind
of questionnaires. Moreover, these APIs allow us to ingest FIHR-first data elements from external EHR systems or any

other medical systems in addition to the ICHOM patient-derived questionnaires. The implementation currently supports multiple clinical trials such as https://CovidImaging.US (IRB-approved) and we are pending IRB approval for our recruitment for the breast cancer (pending IRB approval) implantation guide shared on
GitHub (https://github.com/HL7/fhir-ichom-breast-cancer-ig/)


## Initial setup

Copy `.env.tpl` to `.env` and specify `AIDBOX_LICENSE_ID` and `AIDBOX_LICENSE_KEY`.
[https://license-ui.aidbox.app/](https://license-ui.aidbox.app/)

### Necessary env variables
#### Health Gorilla API
```
HEALTH_GORILLA_CLIENT_ID= (not mandatory)
HEALTH_GORILLA_CLIENT_SECRET=
HEALTH_GORILLA_BASE_URL=https://sandbox.healthgorilla.com or https://api.healthgorilla.com (production)
HEALTH_GORILLA_ISS=https://www.hadleylab.org/ (redirect URL)
HEALTH_GORILLA_SUB=dexter.hadley (HG username)
```

## Cluster setup

### Google Cloud
* Create cluster in google
* Create storage for files
* Add service account for storage: IAM > Service accounts

### K8S
* Create `ServiceAccount` gitlab-admin (using apply -f and the following file)
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: gitlab-admin
  namespace: kube-system
```
* Create `ClusterRoleBinding` gitlab-admin (using apply -f and the following file)
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: gitlab-admin
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
- kind: ServiceAccount
  name: gitlab-admin
  namespace: kube-system
```
* Install helm v3 and add repo:
```
helm repo add stable https://kubernetes-charts.storage.googleapis.com/
```
* Install `nginx-ingress` using helm:
```
helm install nginx-ingress  stable/nginx-ingress --set rbac.create=true --set controller.publishService.enabled=true
```
* Install `cert-manager` following the doc https://cert-manager.io/docs/installation/kubernetes/
* Create ClusterIssuer `letsencrypt-prod`
```
apiVersion: cert-manager.io/v1alpha2
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    email: [INSERT YOUR EMAIL]
    solvers:
    - http01:
        ingress:
          class: nginx
    privateKeySecretRef:
      name: letsencrypt-prod
    server: https://acme-v02.api.letsencrypt.org/directory
```
* Create namespaces using `kubectl create namespace [NAME]`:
  * covidimaging-backend-master
  * covidimaging-backend-staging
  * covidimaging-backend-develop
* Generate secrets using `kubernetes-init-scripts`:
  * Go to directory `cd kubernetes-init-scripts`
  * Run `docker-compose run -e TIER=master --rm init init.sh >> .env`
  * Specify `AIDBOX_LICENSE_ID`, `AIDBOX_LICENSE_KEY`, `BUCKET`, `BUCKET_GCE_KEY` for the current tier in `.env` 
  * Run `docker-compose run -e TIER=master --rm init init-app.sh > app-master.yaml`
  * Run `docker-compose run -e TIER=master --rm init init-aidbox.sh > aidbox-master.yaml`
  * Run `docker-compose run -e TIER=master --rm init init-bucket.sh > bucket-master.yaml`
  * Add `SLACK_URL`, `GCE_ACCOUNT`, `GCE_BUCKET`, `GCE_KEY` for the current tier in  `.env` if you want to use backup job and run:
  ```docker-compose run -e TIER=master --rm init init-backup.sh > backup-master.yaml```
  * Apply all `.yaml` files manually using `kubectl apply -f FILE.yaml`
  * Repeat all actions for each tier: master, staging, develop (you can do it later)

### Gitlab
* Create deploy token
* Create registry secret:
```
kubectl -n demo-staging create secret docker-registry gitlab-registry --docker-username=[DEPLOY TOKEN USERNAME] --docker-password=[DEPLOY TOKEN PASSWORD] --docker-email=[YOUR EMAIL] --docker-server=registry.beda.software
```
3. Fetch token for `gitlab-admin` `ServiceAccount`:
```
kubectl -n kube-system get serviceaccount gitlab-admin -o yaml
```
Get the name of secret and run:
```
kubectl -n kube-system get secret [SECRET NAME] -o yaml
```
Copy base64 encoded token and run
```
echo -n [BASE64 ENCODED TOKEN] | base64 -D
```
4. Setup env variables in CI->Variables for the project
```
TESTS_AIDBOX_LICENSE_ID=ID FOR TESTS PURPOSES
TESTS_AIDBOX_LICENSE_KEY=KEY FOR TESTS PURPOSES
GIT_SUBMODULE_STRATEGY=recursive
K8S_CONFIG=
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: [COPY FROM YOUR ~/.kube/config]
    server: [COPY FROM YOUR ~/.kube/config]
  name: cluster
contexts:
- context:
    cluster: cluster
    user: gitlab-admin
  name: default
users:
- name: gitlab-admin
  user:
    token: [BASE64 DECODED TOKEN FROM PREVIOUS STEP] 
current-context: default
```

### Final step
* Run pipeline for one of branch: `master`, `staging`, `develop`
