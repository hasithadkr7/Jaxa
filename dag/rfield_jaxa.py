from datetime import datetime
from airflow import DAG
from airflow.operators.bash_operator import BashOperator


prod_dag_name = 'jaxa_rfield_dag'
schedule_interval = '00,30 * * * *'
SKIP = 0


cmd = 'gsmap_now.20191014.0700_0759.05_AsiaSS.csv'

create_rfield_cmd = "ssh -i /home/uwcc-admin/.ssh/uwcc-admin -o \"StrictHostKeyChecking no\" uwcc-admin@10.138.0.3 " \
                      "\'bash -c \"/home/uwcc-admin/jaxa/create_jaxa_rfield.sh " \
                      "-d {{ (execution_date).strftime(\"%Y-%m-%d %H:%M:%S\") }} \" \'"

default_args = {
    'owner': 'dss admin',
    'start_date': datetime.strptime('2019-10-14 05:20:00', '%Y-%m-%d %H:%M:%S'),
    'email': ['hasithadkr7@gmail.com'],
    'email_on_failure': True,
}

with DAG(dag_id=prod_dag_name, default_args=default_args, schedule_interval=schedule_interval,
         description='Run DSS Controller DAG') as dag:
    create_rfield = BashOperator(
        task_id='create_rfield',
        bash_command=create_rfield_cmd,
        dag=dag
    )

    create_rfield

