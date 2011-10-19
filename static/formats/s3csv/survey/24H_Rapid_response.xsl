<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         survey-Response - CSV Import Stylesheet

         2011-Jun-28 / Graeme Foster <graeme AT acm DOT org>

         - Specialist transform file for the 24H rapid assessment form
         
         - use for import to survey/question_response resource
         
         - example raw URL usage:
           Let URLpath be the URL to Sahana Eden appliation
           Let Resource be survey/question_response/create
           Let Type be s3csv
           Let CSVPath be the path on the server to the CSV file to be imported
           Let XSLPath be the path on the server to the XSL transform file
           Then in the browser type:
           
           URLpath/Resource.Type?filename=CSVPath&transform=XSLPath
           
           You can add a third argument &ignore_errors

         CSV fields:
         Template..............survey_template.name
         Series................survey_series.name
         24H-BI-1..............survey_response.question_list
         24H-BI-2..............survey_response.question_list
         24H-BI-3..............survey_response.question_list
         24H-BI-4..............survey_response.question_list
         24H-BI-5..............survey_response.question_list
         24H-BI-6..............survey_response.question_list
         24H-BI-7..............survey_response.question_list
         24H-BI-8..............survey_response.question_list
         24H-BI-9..............survey_response.question_list
         24H-BI-10.............survey_response.question_list
         24H-BI-11.............survey_response.question_list
         24H-BI-12.............survey_response.question_list
         24H-BI-13.............survey_response.question_list
         24H-H-1...............survey_response.question_list
         24H-H-2...............survey_response.question_list
         24H-H-3...............survey_response.question_list
         24H-H-4...............survey_response.question_list
         24H-H-5...............survey_response.question_list
         24H-H-6...............survey_response.question_list
         24H-H-7...............survey_response.question_list
         24H-I-1...............survey_response.question_list
         24H-I-2...............survey_response.question_list
         24H-I-3...............survey_response.question_list
         24H-I-4...............survey_response.question_list
         24H-I-5...............survey_response.question_list
         24H-I-6...............survey_response.question_list
         24H-I-7...............survey_response.question_list
         24H-I-8...............survey_response.question_list
         24H-I-9...............survey_response.question_list
         24H-I-10..............survey_response.question_list
         24H-I-11..............survey_response.question_list
         24H-I-12..............survey_response.question_list
         24H-I-13..............survey_response.question_list
         24H-I-14..............survey_response.question_list
         24H-I-15..............survey_response.question_list
         24H-L-1...............survey_response.question_list
         24H-L-2...............survey_response.question_list
         24H-L-3...............survey_response.question_list
         24H-L-4...............survey_response.question_list
         24H-L-5...............survey_response.question_list
         24H-L-6...............survey_response.question_list
         24H-L-7...............survey_response.question_list
         24H-Re-1..............survey_response.question_list
         24H-Re-2..............survey_response.question_list
         24H-Re-3..............survey_response.question_list
         24H-Re-4..............survey_response.question_list
         24H-Re-5..............survey_response.question_list
         24H-Ri-1..............survey_response.question_list
         24H-Ri-2..............survey_response.question_list
         24H-Ri-3..............survey_response.question_list
         24H-Ri-4..............survey_response.question_list
         24H-S-1...............survey_response.question_list
         24H-S-2...............survey_response.question_list
         24H-S-3...............survey_response.question_list
         24H-S-4...............survey_response.question_list
         24H-S-5...............survey_response.question_list
         24H-S-6...............survey_response.question_list
         24H-S-7...............survey_response.question_list
         24H-S-8...............survey_response.question_list
         24H-S-9...............survey_response.question_list


    *********************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- ********************************************************** -->
            <!-- Create each record -->
            <xsl:for-each select="table/row">
                <!-- Create the survey template -->
                <resource name="survey_template">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="col[@field='Template']"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="col[@field='Template']"/></data>
                    <data field="description"><xsl:value-of select="col[@field='Template Description']"/></data>
                    <data field="status"><xsl:value-of select="1"/></data>
                </resource>
                <resource name="survey_series">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="col[@field='Series']"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="col[@field='Series']"/></data>
                    <!-- Link to Template -->
                    <reference field="template_id" resource="survey_template">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="col[@field='Template']"/>
                        </xsl:attribute>
                    </reference>
                </resource>
                <resource name="survey_complete">
                    <data field="answer_list">
<xsl:if test="col[@field='24H-BI-1']!=''">"24H-BI-1","<xsl:value-of select="col[@field='24H-BI-1']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-BI-2']!=''">"24H-BI-2","<xsl:value-of select="col[@field='24H-BI-2']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-BI-3']!=''">"24H-BI-3","<xsl:value-of select="col[@field='24H-BI-3']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-BI-4']!=''">"24H-BI-4","<xsl:value-of select="col[@field='24H-BI-4']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-BI-5']!=''">"24H-BI-5","<xsl:value-of select="col[@field='24H-BI-5']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-BI-6']!=''">"24H-BI-6","<xsl:value-of select="col[@field='24H-BI-6']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-BI-7']!=''">"24H-BI-7","<xsl:value-of select="col[@field='24H-BI-7']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-BI-8']!=''">"24H-BI-8","<xsl:value-of select="col[@field='24H-BI-8']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-BI-9']!=''">"24H-BI-9","<xsl:value-of select="col[@field='24H-BI-9']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-BI-10']!=''">"24H-BI-10","<xsl:value-of select="col[@field='24H-BI-10']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-BI-11']!=''">"24H-BI-11","<xsl:value-of select="col[@field='24H-BI-11']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-BI-12']!=''">"24H-BI-12","<xsl:value-of select="col[@field='24H-BI-12']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-BI-13']!=''">"24H-BI-13","<xsl:value-of select="col[@field='24H-BI-13']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-H-1']!=''">"24H-H-1","<xsl:value-of select="col[@field='24H-H-1']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-H-2']!=''">"24H-H-2","<xsl:value-of select="col[@field='24H-H-2']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-H-3']!=''">"24H-H-3","<xsl:value-of select="col[@field='24H-H-3']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-H-4']!=''">"24H-H-4","<xsl:value-of select="col[@field='24H-H-4']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-H-5']!=''">"24H-H-5","<xsl:value-of select="col[@field='24H-H-5']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-H-6']!=''">"24H-H-6","<xsl:value-of select="col[@field='24H-H-6']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-H-7']!=''">"24H-H-7","<xsl:value-of select="col[@field='24H-H-7']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-I-1']!=''">"24H-I-1","<xsl:value-of select="col[@field='24H-I-1']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-I-2']!=''">"24H-I-2","<xsl:value-of select="col[@field='24H-I-2']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-I-3']!=''">"24H-I-3","<xsl:value-of select="col[@field='24H-I-3']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-I-4']!=''">"24H-I-4","<xsl:value-of select="col[@field='24H-I-4']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-I-5']!=''">"24H-I-5","<xsl:value-of select="col[@field='24H-I-5']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-I-6']!=''">"24H-I-6","<xsl:value-of select="col[@field='24H-I-6']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-I-7']!=''">"24H-I-7","<xsl:value-of select="col[@field='24H-I-7']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-I-8']!=''">"24H-I-8","<xsl:value-of select="col[@field='24H-I-8']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-I-9']!=''">"24H-I-9","<xsl:value-of select="col[@field='24H-I-9']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-I-10']!=''">"24H-I-10","<xsl:value-of select="col[@field='24H-I-10']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-I-11']!=''">"24H-I-11","<xsl:value-of select="col[@field='24H-I-11']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-I-12']!=''">"24H-I-12","<xsl:value-of select="col[@field='24H-I-12']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-I-13']!=''">"24H-I-13","<xsl:value-of select="col[@field='24H-I-13']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-I-14']!=''">"24H-I-14","<xsl:value-of select="col[@field='24H-I-14']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-I-15']!=''">"24H-I-15","<xsl:value-of select="col[@field='24H-I-15']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-L-1']!=''">"24H-L-1","<xsl:value-of select="col[@field='24H-L-1']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-L-2']!=''">"24H-L-2","<xsl:value-of select="col[@field='24H-L-2']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-L-3']!=''">"24H-L-3","<xsl:value-of select="col[@field='24H-L-3']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-L-4']!=''">"24H-L-4","<xsl:value-of select="col[@field='24H-L-4']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-L-5']!=''">"24H-L-5","<xsl:value-of select="col[@field='24H-L-5']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-L-6']!=''">"24H-L-6","<xsl:value-of select="col[@field='24H-L-6']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-L-7']!=''">"24H-L-7","<xsl:value-of select="col[@field='24H-L-7']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-Re-1']!=''">"24H-Re-1","<xsl:value-of select="col[@field='24H-Re-1']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-Re-2']!=''">"24H-Re-2","<xsl:value-of select="col[@field='24H-Re-2']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-Re-3']!=''">"24H-Re-3","<xsl:value-of select="col[@field='24H-Re-3']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-Re-4']!=''">"24H-Re-4","<xsl:value-of select="col[@field='24H-Re-4']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-Re-5']!=''">"24H-Re-5","<xsl:value-of select="col[@field='24H-Re-5']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-Ri-1']!=''">"24H-Ri-1","<xsl:value-of select="col[@field='24H-Ri-1']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-Ri-2']!=''">"24H-Ri-2","<xsl:value-of select="col[@field='24H-Ri-2']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-Ri-3']!=''">"24H-Ri-3","<xsl:value-of select="col[@field='24H-Ri-3']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-Ri-4']!=''">"24H-Ri-4","<xsl:value-of select="col[@field='24H-Ri-4']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-S-1']!=''">"24H-S-1","<xsl:value-of select="col[@field='24H-S-1']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-S-2']!=''">"24H-S-2","<xsl:value-of select="col[@field='24H-S-2']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-S-3']!=''">"24H-S-3","<xsl:value-of select="col[@field='24H-S-3']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-S-4']!=''">"24H-S-4","<xsl:value-of select="col[@field='24H-S-4']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-S-5']!=''">"24H-S-5","<xsl:value-of select="col[@field='24H-S-5']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-S-6']!=''">"24H-S-6","<xsl:value-of select="col[@field='24H-S-6']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-S-7']!=''">"24H-S-7","<xsl:value-of select="col[@field='24H-S-7']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-S-8']!=''">"24H-S-8","<xsl:value-of select="col[@field='24H-S-8']"/>"
</xsl:if>
<xsl:if test="col[@field='24H-S-9']!=''">"24H-S-9","<xsl:value-of select="col[@field='24H-S-9']"/>"
</xsl:if>
</data>   
                    <!-- Link to Series -->
                    <reference field="series_id" resource="survey_series">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="col[@field='Series']"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:for-each>
        </s3xml>
    </xsl:template>
</xsl:stylesheet>
