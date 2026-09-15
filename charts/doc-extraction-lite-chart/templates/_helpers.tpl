{{- define "doc-extraction-lite.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "doc-extraction-lite.fullname" -}}
{{- default .Release.Name .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "doc-extraction-lite.labels" -}}
app.kubernetes.io/name: {{ include "doc-extraction-lite.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" }}
{{- end -}}

{{- define "doc-extraction-lite.selectorLabels" -}}
app.kubernetes.io/name: {{ include "doc-extraction-lite.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
