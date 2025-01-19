
from src.agent_task_mgr.state import AgentState
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta


def visalize_project_timeline(final_state: AgentState):
    number_of_iterations = final_state['iteration_number']

    for i in range(number_of_iterations):
        ## Tasks schedule
        task_schedules = final_state['schedule_iteration'][i].schedule

        t = []
        # Iterate over the task_schedules and append each task's data to the DataFrame
        for task_schedule in task_schedules:
            t.append([
                task_schedule.task.task_name,
                task_schedule.start_day,
                task_schedule.end_day
            ])

        df_schedule = pd.DataFrame(t,columns=['task_name', 'start', 'end'])

        ## Tasks allocation
        task_allocations = final_state['task_allocations_iteration'][i].task_allocations

        t = []
        # Iterate over the task_schedules and append each task's data to the DataFrame
        for task_allocation in task_allocations:
            t.append([
                task_allocation.task.task_name,
                task_allocation.team_member.name
            ])

        df_allocation = pd.DataFrame(t,columns=['task_name', 'team_member'])

        df = df_allocation.merge(df_schedule, on='task_name')

        
        # Get the current date
        current_date = datetime.today()

        # Convert start and end offsets to actual dates
        df['start'] = df['start'].apply(lambda x: current_date + timedelta(days=x))
        df['end'] = df['end'].apply(lambda x: current_date + timedelta(days=x))

        df.rename(columns={'team_member': 'Team Member'}, inplace=True)
        df.sort_values(by='Team Member', inplace=True)
        # Create a Gantt chart
        fig = px.timeline(df, x_start="start", x_end="end", y="task_name", color="Team Member", title=f"Gantt Chart - Iteration:{i+1} ")

        # Update layout for better visualization
        fig.update_layout(
            xaxis_title="Timeline",
            yaxis_title="Tasks",
            yaxis=dict(autorange="reversed"),  # Reverse the y-axis to have tasks in the vertical side
            title_x=0.5
        )
        fig.write_image(f'logs/gantt_chart_iteration_{i+1}.png')
        # Show the plot
        # fig.show()
        # return fig