# Generated by Django 4.2.1 on 2024-07-31 21:36

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import projectmanagement.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('partners', '0002_initial'),
        ('masterdata', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('locations', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=160, null=True)),
                ('project_id', models.CharField(blank=True, max_length=155, null=True, unique=True)),
                ('project_status', models.CharField(choices=[('todo', 'TODO'), ('inprogress', 'INPROGRESS'), ('complete', 'COMPLETE')], default='todo', max_length=100)),
                ('start_date', models.DateField(null=True)),
                ('end_date', models.DateField(null=True)),
                ('project_estimation', models.IntegerField(null=True)),
                ('total_target_kWp', models.CharField(default=0, max_length=160)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('location_id', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='locations.location')),
            ],
        ),
        migrations.CreateModel(
            name='ProjectPhase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phase_name', models.CharField(max_length=160)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('target_kWp', models.CharField(blank=True, max_length=160, null=True)),
                ('phase_status', models.CharField(choices=[('todo', 'TODO'), ('inprogress', 'INPROGRESS'), ('complete', 'COMPLETE')], default='todo', max_length=100)),
                ('target_count', models.IntegerField(blank=True, null=True)),
                ('target_duration', models.CharField(choices=[('days', 'Days'), ('weeks', 'Weeks'), ('months', 'Months'), ('years', 'Years')], max_length=100, null=True)),
                ('final_output', models.CharField(blank=True, max_length=55, null=True)),
                ('order_number', models.IntegerField(blank=True, null=True)),
                ('phase_estimation', models.IntegerField(blank=True, null=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('project_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projectmanagement.project')),
            ],
        ),
        migrations.CreateModel(
            name='ProjectPhaseTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=160)),
                ('description', models.TextField(blank=True, null=True)),
                ('assigned_at', models.DateTimeField(null=True)),
                ('expected_complete_date', models.DateField(blank=True, null=True)),
                ('status', models.CharField(choices=[('todo', 'TODO'), ('inprogress', 'INPROGRESS'), ('review', 'REVIEW'), ('complete', 'COMPLETE')], default='todo', max_length=100)),
                ('order_number', models.IntegerField(null=True)),
                ('is_dependent', models.BooleanField(default=False)),
                ('dependent_task_type', models.CharField(blank=True, choices=[('phasestarttime', 'PHASESTARTTIME'), ('task', 'TASK')], max_length=100, null=True)),
                ('dependent_count', models.IntegerField(blank=True, null=True)),
                ('dependent_duration', models.CharField(blank=True, choices=[('days', 'Days'), ('weeks', 'Weeks'), ('months', 'Months'), ('years', 'Years')], max_length=100, null=True)),
                ('priority_level', models.CharField(choices=[('low', 'LOW'), ('medium', 'MEDIUM'), ('high', 'HIGH')], default='low', max_length=100)),
                ('cost_estimations_pv', models.IntegerField(null=True)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('target_count', models.IntegerField(blank=True, null=True)),
                ('target_duration', models.CharField(blank=True, choices=[('days', 'Days'), ('weeks', 'Weeks'), ('months', 'Months'), ('years', 'Years')], max_length=100, null=True)),
                ('phase_start_confirmation', models.BooleanField(default=True)),
                ('assigned_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_by', to=settings.AUTH_USER_MODEL)),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='partners.partner')),
                ('assigned_to_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('completed_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='completed_by', to=settings.AUTH_USER_MODEL)),
                ('parent_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='parent', to='projectmanagement.projectphasetask')),
                ('project_phase_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='projectmanagement.projectphase')),
            ],
        ),
        migrations.CreateModel(
            name='ProjectPhaseTaskTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=160)),
                ('description', models.TextField(null=True)),
                ('order_number', models.IntegerField(null=True)),
                ('is_dependent', models.BooleanField(default=False)),
                ('dependent_task_type', models.CharField(choices=[('phasestarttime', 'PHASESTARTTIME'), ('task', 'TASK')], max_length=100, null=True)),
                ('dependent_count', models.IntegerField(blank=True, null=True)),
                ('dependent_duration', models.CharField(choices=[('days', 'Days'), ('weeks', 'Weeks'), ('months', 'Months'), ('years', 'Years')], max_length=100, null=True)),
                ('priority_level', models.CharField(choices=[('low', 'LOW'), ('medium', 'MEDIUM'), ('high', 'HIGH')], max_length=100, null=True)),
                ('expected_count', models.IntegerField(blank=True, null=True)),
                ('expected_duration', models.CharField(choices=[('days', 'Days'), ('weeks', 'Weeks'), ('months', 'Months'), ('years', 'Years')], max_length=100, null=True)),
                ('assigned_to_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='partners.type')),
                ('parent_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='parenttemplate', to='projectmanagement.projectphasetasktemplate')),
            ],
        ),
        migrations.CreateModel(
            name='ProjectTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('template_type', models.CharField(choices=[('project', 'PROJECT'), ('phase', 'PHASE')], max_length=100)),
                ('status', models.CharField(choices=[('draft', 'draft'), ('published', 'published')], max_length=100, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='TemplateTaskFields',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_required', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('field_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='masterdata.field')),
                ('project_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projectmanagement.projecttemplate')),
                ('task_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projectmanagement.projectphasetasktemplate')),
            ],
        ),
        migrations.CreateModel(
            name='TaskUpdate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('column_name', models.CharField(max_length=55, null=True)),
                ('updated_date', models.DateTimeField()),
                ('task_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='projectmanagement.projectphasetask')),
                ('user_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='TaskFields',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_required', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('field_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='masterdata.field')),
                ('project_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projectmanagement.project')),
                ('task_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projectmanagement.projectphasetask')),
            ],
        ),
        migrations.CreateModel(
            name='TaskAssignedUsers',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('assigned_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_by_user', to=settings.AUTH_USER_MODEL)),
                ('task_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projectmanagement.projectphasetask')),
                ('user_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assign_to_user', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ProjectPhaseTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phase_name', models.CharField(max_length=255)),
                ('target_count', models.IntegerField(null=True)),
                ('target_duration', models.CharField(choices=[('days', 'Days'), ('weeks', 'Weeks'), ('months', 'Months'), ('years', 'Years')], max_length=100, null=True)),
                ('order_number', models.IntegerField(null=True)),
                ('template_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projectmanagement.projecttemplate')),
            ],
        ),
        migrations.CreateModel(
            name='ProjectPhaseTaskTemplateDependency',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('condition', models.CharField(choices=[('and', 'AND'), ('or', 'OR')], max_length=100, null=True)),
                ('dependent_task_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='dependent_tasks_template', to='projectmanagement.projectphasetasktemplate')),
                ('task_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='task_templates', to='projectmanagement.projectphasetasktemplate')),
            ],
            options={
                'verbose_name_plural': 'Project phase task template dependencies',
            },
        ),
        migrations.AddField(
            model_name='projectphasetasktemplate',
            name='project_phases_template_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projectmanagement.projectphasetemplate'),
        ),
        migrations.CreateModel(
            name='ProjectPhaseTaskMentions',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('mentioned_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='mentioned_by', to=settings.AUTH_USER_MODEL)),
                ('task_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projectmanagement.projectphasetask')),
                ('user_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mentioned_to', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Project phase task mentions',
            },
        ),
        migrations.CreateModel(
            name='ProjectPhaseTaskDependency',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('condition', models.CharField(choices=[('and', 'AND'), ('or', 'OR')], max_length=100, null=True)),
                ('dependent_task_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='dependent_tasks', to='projectmanagement.projectphasetask')),
                ('task_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='dependent', to='projectmanagement.projectphasetask')),
            ],
            options={
                'verbose_name_plural': 'Project phase task dependencies',
            },
        ),
        migrations.CreateModel(
            name='ProjectPhasesTaskFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file_url', models.FileField(blank=True, null=True, upload_to='files/projectphasetaskfiles', validators=[projectmanagement.models.validate_file_size])),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('project_phase_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='projectmanagement.projectphase')),
                ('project_phase_task_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='projectmanagement.projectphasetask')),
            ],
        ),
        migrations.CreateModel(
            name='PhaseUpdate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('column_name', models.CharField(max_length=55, null=True)),
                ('updated_date', models.DateTimeField()),
                ('phase_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='projectmanagement.projectphase')),
                ('user_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
