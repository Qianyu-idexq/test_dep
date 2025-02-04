import requests
import json
import os
import sys



server_host = sys.argv[1]
token       = sys.argv[2]
tag         = sys.argv[3]
root        = sys.argv[4]
project     = sys.argv[5]
env         = sys.argv[6]
warehause_id= sys.argv[7]
secret      = sys.argv[8]
client      = sys.argv[9]
tenant      = sys.argv[10]
#url = f'https://{server_host}.azuredatabricks.net/api/2.2/jobs/'
#header = {'Authorization': f'Bearer {token}'}
#path = root + '/dbx/workflows/'+project+'/'



new_job = [
      {
        "job_cluster_key": "dbt_CLI",
        "new_cluster": {
          "spark_version": "15.4.x-scala2.12",
          "spark_conf": {
            "spark.master": "local[*, 4]",
            "spark.databricks.cluster.profile": "singleNode"
          },
          "azure_attributes": {
            "first_on_demand": 1,
            "availability": "ON_DEMAND_AZURE",
            "spot_bid_max_price": -1
          },
          "node_type_id": "Standard_DS3_v2",
          "driver_node_type_id": "Standard_DS3_v2",
          "custom_tags": {
            "ResourceClass": "SingleNode"
          },
          "spark_env_vars": {
            "PYSPARK_PYTHON": "/databricks/python3/bin/python3"
          },
          "enable_elastic_disk": True,
          "data_security_mode": "SINGLE_USER",
          "runtime_engine": "STANDARD",
          "num_workers": 0
        }
      }
    ]

libraries = [
        {
          "pypi": {
            "package": "dbt-databricks==1.8.3"
          }
        }
      ]

def app_re_token(client,secret,tenant):

    d = {

        "client_id": client,
        "client_secret": secret,
        "grant_type": "client_credentials",
        'scope': 'all-apis'
    
    }
    
    headers = {'Content-type': 'application/x-www-form-urlencoded'}
    
    token = requests.post(f'https://{server_host}.azuredatabricks.net/oidc/v1/token', headers=headers, data=d)
    print(token.json())

    api_key = token.json()['access_token']

    return api_key



token = app_re_token(client,secret,tenant)

url = f'https://{server_host}.azuredatabricks.net/api/2.2/jobs/'
header = {'Authorization': f'Bearer {token}'}
path = root + '/dbx/workflows/'+project+'/'

def workflow_dploy(d):
    # change parameter of workflow
    d['git_source']['git_tag'] = d['git_source'].pop('git_branch')
    d['git_source']['git_tag'] = tag
    try:
        print(d['run_as']['service_principal_name'])
    except:
        d['run_as']['service_principal_name'] = d['run_as'].pop('user_name')
        d['run_as']['service_principal_name'] = client
    for i in range(len(d['tasks'])):
        if 'dbt_task' in d['tasks'][i]:
            d['tasks'][i]['dbt_task']['schema'] = env
            d['tasks'][i]['dbt_task']['warehouse_id'] = warehause_id
            d['tasks'][i]['job_cluster_key']= 'dbt_CLI'
            d['tasks'][i]['libraries'] = libraries
            try:
                d['tasks'][i].pop('environment_key')
            except:
                pass
    d['job_clusters'] = new_job
    
    d['name'] = d['name'] + '_QA'
    job_name = d['name']
    print(json.dumps(d))
    d_dump = json.dumps(d)
    
    #update if exist workflow
    flag = 0
    lists = requests.get(url+'list', headers=header)
    try:
        job_json = lists.json()['jobs']
        job_lists = {}
        
        for i in job_json:
            job_lists[i['job_id']] = i['settings']['name']
            if i['settings']['name'] == job_name:
                flag = 1
                job_id = i['job_id']
    except:
        print("Empty Response")
    
    # add workflow
    if flag == 0:
        token = requests.post(url+'create', headers=header, data=d_dump)
    elif flag == 1:
        data = {"job_id": job_id,
                "new_settings": d}
        token = requests.post(url+'reset', headers=header, data=json.dumps(data))
    print(token.json())

for file in os.listdir(path):
    with open(path+file) as f:
        d = json.load(f)
        workflow_dploy(d)
