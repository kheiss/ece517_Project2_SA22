<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         survey-Template - CSV Import Stylesheet

         2011-Jun-16 / Graeme Foster <graeme AT acm DOT org>

         - use for import to survey/question_metadata resource
         
         - example raw URL usage:
           Let URLpath be the URL to Sahana Eden appliation
           Let Resource be survey/question_metadata/create
           Let Type be s3csv
           Let CSVPath be the path on the server to the CSV file to be imported
           Let XSLPath be the path on the server to the XSL transform file
           Then in the browser type:
           
           URLpath/Resource.Type?filename=CSVPath&transform=XSLPath
           
           You can add a third argument &ignore_errors

         CSV fields:
         Question..............survey_question.name
         Question Type.........survey_question.type
         Question Notes........survey_question.notes
         Question Code.........survey_question.code
         metaD1................survey_question_metadata.descriptor
         metaV1................survey_question_metadata.value
         metaD2................survey_question_metadata.descriptor
         metaV2................survey_question_metadata.value
         metaD3................survey_question_metadata.descriptor
         metaV3................survey_question_metadata.value


    *********************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- ********************************************************** -->
            <!-- Create each record -->
            <xsl:for-each select="table/row">
                <resource name="survey_question">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="col[@field='Question']"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="col[@field='Question']"/></data>
                    <data field="type"><xsl:value-of select="col[@field='Question Type']"/></data>
                    <data field="code"><xsl:value-of select="col[@field='Question Code']"/></data>
                    <data field="notes"><xsl:value-of select="col[@field='Question Notes']"/></data>
                </resource>
                <xsl:if test="col[@field='metaD1']!=''">
                    <resource name="survey_question_metadata">
                        <data field="descriptor"><xsl:value-of select="col[@field='metaD1']"/></data>
                        <xsl:choose>
                            <xsl:when test="col[@field='metaV1']=''">
                                <data field="value">None</data>
                            </xsl:when>
                            <xsl:otherwise test="col[@field='metaV1']=''">
                                <data field="value"><xsl:value-of select="col[@field='metaV1']"/></data>
                            </xsl:otherwise>
                        </xsl:choose>
                        <!-- Link to Questions -->
                        <reference field="question_id" resource="survey_question">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="col[@field='Question']"/>
                            </xsl:attribute>
                        </reference>
                    </resource>
                </xsl:if>
                <xsl:if test="col[@field='metaD2']!=''">
                    <resource name="survey_question_metadata">
                        <data field="descriptor"><xsl:value-of select="col[@field='metaD2']"/></data>
                        <xsl:choose>
                            <xsl:when test="col[@field='metaV2']=''">
                                <data field="value">None</data>
                            </xsl:when>
                            <xsl:otherwise test="col[@field='metaV2']=''">
                                <data field="value"><xsl:value-of select="col[@field='metaV2']"/></data>
                            </xsl:otherwise>
                        </xsl:choose>
                        <!-- Link to Questions -->
                        <reference field="question_id" resource="survey_question">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="col[@field='Question']"/>
                            </xsl:attribute>
                        </reference>
                    </resource>
                </xsl:if>
                <xsl:if test="col[@field='metaD3']!=''">
                    <resource name="survey_question_metadata">
                        <data field="descriptor"><xsl:value-of select="col[@field='metaD3']"/></data>
                        <xsl:choose>
                            <xsl:when test="col[@field='metaV3']=''">
                                <data field="value">None</data>
                            </xsl:when>
                            <xsl:otherwise test="col[@field='metaV3']=''">
                                <data field="value"><xsl:value-of select="col[@field='metaV3']"/></data>
                            </xsl:otherwise>
                        </xsl:choose>
                        <!-- Link to Questions -->
                        <reference field="question_id" resource="survey_question">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="col[@field='Question']"/>
                            </xsl:attribute>
                        </reference>
                    </resource>
                </xsl:if>
            </xsl:for-each>
        </s3xml>
    </xsl:template>
</xsl:stylesheet>
