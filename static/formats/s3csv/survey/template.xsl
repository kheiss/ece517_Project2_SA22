<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         survey-Template - CSV Import Stylesheet

         2011-Jun-16 / Graeme Foster <graeme AT acm DOT org>

         - use for import to survey/template resource
         
         - example raw URL usage:
           Let URLpath be the URL to Sahana Eden appliation
           Let Resource be survey/template/create
           Let Type be s3csv
           Let CSVPath be the path on the server to the CSV file to be imported
           Let XSLPath be the path on the server to the XSL transform file
           Then in the browser type:
           
           URLpath/Resource.Type?filename=CSVPath&transform=XSLPath
           
           You can add a third argument &ignore_errors

         CSV fields:
         Name...................survey_template.name
         Description............survey_template.description
         Status.................survey_template.status
         Complete Question......survey_template.competion_qstn
         Date Question..........survey_template.date_qstn
         Time Question..........survey_template.time_qstn
         Location Question......survey_template.location_qstn
         Priority Question......survey_template.priority_qstn



    *********************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- ********************************************************** -->
            <!-- Create each record -->
            <xsl:for-each select="table/row">
                <!-- Create the survey template -->
                <resource name="survey_template">
                    <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
                    <data field="description"><xsl:value-of select="col[@field='Description']"/></data>
                    <data field="status"><xsl:value-of select="col[@field='Status']"/></data>
                    <data field="competion_qstn"><xsl:value-of select="col[@field='Complete Question']"/></data>
                    <data field="date_qstn"><xsl:value-of select="col[@field='Date Question']"/></data>
                    <data field="time_qstn"><xsl:value-of select="col[@field='Time Question']"/></data>
                    <data field="location_qstn"><xsl:value-of select="col[@field='Location Question']"/></data>
                    <data field="priority_qstn"><xsl:value-of select="col[@field='Priority Question']"/></data>
                </resource>
            </xsl:for-each>
        </s3xml>
    </xsl:template>
</xsl:stylesheet>
