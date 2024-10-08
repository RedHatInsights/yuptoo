# Ephemeral Environment

First make sure you have access to the ephemeral cluster and install a bonfire and oc binary in the PATH. For more details regarding getting access and setup, please go through the [documentation - Onboarding to the Ephemeral Cluster](https://consoledot.pages.redhat.com/docs/dev/getting-started/ephemeral/onboarding.html)

## Run Yuptoo in Ephemeral Environment

Login to the ephemeral cluster by grabbing a login command from the [token request page](https://oauth-openshift.apps.c-rh-c-eph.8p0c.p1.openshiftapps.com/oauth/token/request)

    oc login --token=sha256~xxxxxx --server=https://api.c-rh-c-eph.8p0c.p1.openshiftapps.com:6443

Run bonfire command to reserve the ephemeral namespace and to deploy yuptoo in that namespace

    bonfire deploy yuptoo

Note down the name of reserved namespace from the output of above bonfire command. 

Make sure all the pods are running. One can use below command to verify it. 

    oc get pods -n <reserved-namespace>

Below command can be used to follow the yuptoo process logs. 

    oc logs -f yuptoo-yuptoo-service-xxxxxx -n <reserved-namespace>

## Upload tarball to yuptoo in Ephemeral Environment

    make sample-data
    make ephemeral-upload-data file=temp/sample_data_ready_******.tar.gz env=<reserved-namespace>
