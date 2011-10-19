<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         survey-answer - CSV Import Stylesheet

         2011-Jun-16 / Graeme Foster <graeme AT acm DOT org>

         - use for import to survey/answer resource
         
         - example raw URL usage:
           Let URLpath be the URL to Sahana Eden appliation
           Let Resource be survey/answer/create
           Let Type be s3csv
           Let CSVPath be the path on the server to the CSV file to be imported
           Let XSLPath be the path on the server to the XSL transform file
           Then in the browser type:
           
           URLpath/Resource.Type?filename=CSVPath&transform=XSLPath
           
           You can add a third argument &ignore_errors

         CSV fields:
         complete_id.......survey_answer.complete_id
         question_code.....survey_answer.question_id
         value.............survey_answer.value

    *********************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- ********************************************************** -->
            <!-- Create each record -->
            <xsl:for-each select="table/row">
                <resource name="survey_question">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="col[@field='question_code']"/>
                    </xsl:attribute>
                    <data field="code"><xsl:value-of select="col[@field='question_code']"/></data>
                </resource>
                <!-- Lookup table survey_template -->
                <resource name="survey_answer">
                    <data field="value"><xsl:value-of select="col[@field='value']"/></data>
                    <data field="complete_id"><xsl:value-of select="col[@field='complete_id']"/></data>
                    <!-- Link to Template -->
                    <reference field="question_id" resource="survey_question">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="col[@field='question_code']"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:for-each>
        </s3xml>
    </xsl:template>
</xsl:stylesheet>
