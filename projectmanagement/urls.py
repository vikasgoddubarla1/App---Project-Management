from django.urls import path
from .views import *

urlpatterns = [    
    #--------------------------------------- PROJECT MANAGEMENT URLS --------------------------------------
    path('v1/project/create', ProjectCreate.as_view(), name = 'project-create'),
    path('v1/project/<int:pk>', ProjectUpdate.as_view(), name = 'project-update'), #project_id as pk
    path('v1/project', ProjectList.as_view(), name = 'project-list'),
    path('v1/project/detail/<int:pk>', ProjectDetail.as_view(), name = 'project-details'), #project_id as pk
    path('v1/project/phase/create/<int:project_id>', ProjectPhaseCreate.as_view(), name = 'project-phase-create'),
    path('v1/project/phase/<int:pk>', ProjectPhaseUpdate.as_view(), name = 'project-phase-Update-and-delete'), #project-phase-id as pk
    path('v1/project/phase/status/<int:pk>', ProjectPhaseStatus.as_view(), name = 'project-phase-status-Update'),
    path('v1/project/phase/detail/<int:pk>', ProjectPhaseDetail.as_view(), name = 'project-phase-details'),
    
    
    path('v1/project/phase/task/<int:project_phase_id>', ProjectPhaseTaskCreate.as_view(), name = 'project-phase-task-create'),
    path('v1/project/phase/subTask/<int:parent_id>', ProjectPhaseSubTaskCreate.as_view(), name = 'project-phase-task-create'),
    path('v1/project/phase/task/status/<int:pk>', ProjectPhaseTaskStatus.as_view(), name = 'project-phase-task-status-Update'),
    path('v1/project/phase/task/assignee/<int:pk>', ProjectPhaseTaskAssignee.as_view(), name = 'project-phase-assignee-Update'),
    path('v1/project/phase/task/customer/assign/<int:pk>', ProjectPhaseTaskCustomerAssign.as_view(), name = 'project-phase-customer-assign-Update'),
    path('v1/project/phase/task/general/<int:pk>', ProjectPhaseTaskGeneral.as_view(), name = 'project-phase-assignee-Update'),
    path('v1/project/phase/task/estimation/<int:pk>', ProjectPhaseTaskEstimation.as_view(), name = 'project-phase-assignee-Update'),
    path('v1/project/phase/task/delete/<int:pk>', ProjectPhaseTaskDelete.as_view(), name = 'project-phase-assignee-Update'),
    path('v1/project/phase/task/dependency/<int:pk>', ProjectPhaseTaskDependencyUpdate.as_view(), name = 'project-phase-dependency-Update'),####
    path('v1/project/phase/task/file/<int:project_phase_id>/<int:project_phase_task_id>', ProjectPhasesTaskFileCreate.as_view(), name = 'project-phase-File-Create'),
    path('v1/project/phase/task/file/delete/<int:project_phase_id>/<project_phase_task_id>/<int:file_id>', ProjectPhasesTaskFileDelete.as_view(), name = 'project-phase-File-Delete'),
    path('v1/project/task/get/<int:project_id>', ProjectTaskGetList.as_view(), name='Project-task-list'),
    path('v1/project/phase/task/get/<int:phase_id>', PhaseTaskGetList.as_view(), name='phase-task-list'),
    path('v1/project/phase/task/detail/<int:pk>', ProjectPhaseTaskDetail.as_view(), name = 'project-phase-task-details'),
    # path('v1/project/phase/task/template/dependency/<task_id>', ProjectPhaseTaskDependencyTemplateCreateView.as_view(), name = "template-dependency-create"),
    
    
    
    
    #---------------------------------------- PROJECT TEMPLATE URLS ------------------------------------------------------------------
    path('v1/project/template/create', ProjectTemplateCreate.as_view(), name = 'project-template-create'),
    path('v1/project/template/<int:pk>', ProjectTemplateUpdate.as_view(), name = 'project-template-update'), #project_template_id as pk
    path('v1/project/template', ProjectTemplateList.as_view(), name = 'project-template-list'),
    path('v1/project/template/detail/<int:pk>', ProjectTemplateDetail.as_view(), name = 'project-template-Detail-Delete'),
    path('v1/project/template/delete/<int:pk>', ProjectTemplateDetail.as_view(), name = 'project-template-Detail-Delete'),
    path('v1/project/phase/task/template/create/<int:project_phases_template_id>', ProjectPhaseTaskTemplateCreate.as_view()),
    #----------------------------------------- PROJECT PHASE TEMPLATE URLS ------------------------------------------------------------
    path('v1/project/phase/template/create/<int:template_id>', ProjectPhaseTemplateCreate.as_view(), name = 'project-phase-template-create'),
    path('v1/project/phase/template/<int:pk>', ProjectPhaseTemplateUpdate.as_view(), name = 'project-phase-template-update'),
    path('v1/project/phase/template/delete/<int:pk>', ProjectPhaseTemplateDelete.as_view(), name = 'project-template-Delete'),
    path('v1/project/phase/template/detail/<int:pk>', ProjectPhaseTemplateDetail.as_view(), name = 'project-phase-template-details'),
    
    #--------------------------------------------- PROJECT PHASE TASK TEMPLATE URLS ----------------------------------------------------
    path('v1/project/create/<int:project_id>', ProjectTemplateCreateAfterProject.as_view(), name = 'project-phase-template-create'),
    path('v1/project/task/phase/template/<int:pk>', ProjectPhaseTaskTemplateUpdate.as_view(), name = 'project-phase-template-task-update'),
    path('v1/project/phase/task/template/delete/<int:pk>', ProjectPhaseTaskTemplateDelete.as_view(), name = 'project-template-task-Delete'),
    path('v1/project/template/task/get/<int:template_id>', ProjectTemplateTaskList.as_view(), name='Project-Template_task_list'),
    path('v1/project/phase/template/task/get/<int:phase_id>', PhaseTemplateTaskList.as_view(), name='Project-Template_task_list'),
    # path('v1/project/task/get/<int:project_id>', ProjectPhaseTaskList.as_view(), name='Project-task-list'),
    path('v1/project/phase/excel', ProjectPhaseExcelList.as_view(), name='Project-Template_task_list'),
    path('v1/project/phase/task/template/detail/<int:pk>', ProjectPhaseTaskTemplateDetail.as_view(), name = 'project-phase-task-template-details'),
    
    
    #---------------------------------------------- SORTING VIEWS ---------------------------------------------------------------------
    path('v1/project/template/sorting/<int:project_template_id>/<int:project_phase_template_id>', TemplateTaskSorting.as_view(), name='template-sorting-list'),
    path('v1/project/task/sorting/<int:project_id>/<int:project_phase_id>', ProjectTaskSorting.as_view(), name='project-sorting-list'),
    
    #---------------------------------------------- PROJECT PHASE START DATE API ---------------------------------------------------------------------
    path('v1/project/phase/start/<int:pk>', ProjectPhaseStart.as_view(), name='project-phase-start-date'),
    
    #----------------------------------------------- PHASE UPDATE LIST APIS ----------------------------------------------------------
    path('v1/project/phase/update/list/<int:phase_id>', PhaseUpdateList.as_view(), name='phase-update-list'),
    path('v1/project/phase/task/update/list/<int:task_id>', TaskUpdateList.as_view(), name='phase-task-update-list'),
    
    #------------------------------------------- PROJECT TEMPLATE DUPLICATE APIS ----------------------------------------------------
    path('v1/project/template/duplicate/<int:template_id>', ProjectTemplateDuplicate.as_view(), name='project-template-duplicate'),
    path('v1/project/phase/template/duplicate/<int:phase_template_id>', ProjectPhaseTemplateDuplicate.as_view(), name='project-phase-template-duplicate'),
    
    #-------------------------------------------- PHASE TASK DEPENDENCY APIS -----------------------------------------------------------
    # path('v1/phase/task/dependency/<int:task_id>', ProjectPhaseTaskDependencyCreate.as_view(), name= 'project-phase-task-dependency-create'),
    path('v1/taskList/user', TaskListByUser.as_view(), name='task-list-by-user'),
    path('v1/taskList/location/user', TaskListByLocationStatus.as_view(), name='task-list-by-location-status'),
    
    #------------------------------------------- TASK MENTIONS ----------------------------------------------------------------------
    path('v1/project/phase/task/mentions/create', TaskMentionsCreate.as_view(), name='task-mentions-create'),
    path('v1/project/phase/task/assign', AssignUserTask.as_view(), name='assign_user_task'),
    path('v1/project/dashboard/list', DashBoardProjectList.as_view(), name='project-dashboard-list'),
    
    #--------------------------------------------------- TASKFIELDS AND TASK TEMPLATE FIELDS ---------------------------------------------
    path('v1/taskFields/create', CreateTaskFields.as_view(), name='task-fields-create'),
    path('v1/taskFields/list/<int:task_id>', ListTaskFields.as_view(), name='task-fields-list'),
    path('v1/taskFields/update/<int:pk>', UpdateTaskFields.as_view(), name='task-fields-update'),
    path('v1/taskFields/delete/<int:pk>', DeleteTaskFields.as_view(), name='task-fields-delete'),
    path('v1/taskTemplateFields/create', CreateTaskTemplateFields.as_view(), name='task-template-fields-create'),
    path('v1/taskTemplateFields/list/<int:task_id>', ListTaskTemplateFields.as_view(), name='task-template-fields-list'),
    path('v1/taskTemplateFields/update/<int:pk>', UpdateTemplateTaskFields.as_view(), name='task-template-fields-update'),
    path('v1/taskTemplateFields/delete/<int:pk>', DeleteTaskTemplateFields.as_view(), name='task-template-fields-delete'),
    
]