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
           Let Resource be survey/complete/create
           Let Type be s3csv
           Let CSVPath be the path on the server to the CSV file to be imported
           Let XSLPath be the path on the server to the XSL transform file
           Then in the browser type:
           
           URLpath/Resource.Type?filename=CSVPath&transform=XSLPath
           
           You can add a third argument &ignore_errors

         CSV fields:
         Template..............survey_template.name
         Series................survey_series.name
         <question code>.......survey_response.question_list

    *********************************************************************** -->
    <xsl:template match="/">
      <s3xml>
        <xsl:for-each select="table/row">
            <!-- Create the survey template -->
            <resource name="survey_template">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Template']"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="col[@field='Template']"/></data>
                <data field="description"><xsl:value-of select="col[@field='Template Description']"/></data>
                <data field="status"><xsl:value-of select="2"/></data>
            </resource>
            <!-- Create the survey series -->
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
            <xsl:for-each select="col">
                <xsl:choose>
                  <xsl:when test="@field = 'Template'">
                    <xsl:variable name="Template" select="col[@field='Template']"/>
                  </xsl:when>
                  <xsl:when test="@field = 'Series'">
                    <xsl:variable name="Series" select="col[@field='Series']"/>
                  </xsl:when>
                  <xsl:otherwise>
<xsl:if test=".!=''">"<xsl:value-of select="@field"/>","<xsl:value-of select="."/>"
</xsl:if>
                  </xsl:otherwise>
                </xsl:choose>
            </xsl:for-each>
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
