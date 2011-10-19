$(document).ready(function() {
    // Competency Field
    S3FilterFieldChange({
		'FilterField':	'skill_id',
		'Field':		'competency_id',
		'FieldResource':'competency',
		'FieldPrefix':	'hrm',
	    'url':		 	S3.Ap.concat('/hrm/skill_competencies/'),
		'msgNoRecords':	S3.i18n.no_ratings
	});
});