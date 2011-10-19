<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
    
    <!-- **********************************************************************
         Item Categories - CSV Import Stylesheet

         - example raw URL usage:
           Let URLpath be the URL to Sahana Eden appliation
           Let Resource be hrm/competency_rating/create
           Let Type be s3csv
           Let CSVPath be the path on the server to the CSV file to be imported
           Let XSLPath be the path on the server to the XSL transform file
           Then in the browser type:
           
           URLpath/Resource.Type?filename=CSVPath&transform=XSLPath
           
           You can add a third argument &ignore_errors
         CSV fields:
         skill type......................hrm_skill_type.name
         name............................hrm_competency_rating.name
         priority........................hrm_competency_rating.priority

    *********************************************************************** -->

    <xsl:output method="xml"/>

    <xsl:template match="/">
        <s3xml>
            <!-- Create each record -->
            <xsl:for-each select="table/row">
    
                <!-- HRM Skill Type -->
                <xsl:variable name="SkillType"><xsl:value-of select="col[@field='skill type']"/></xsl:variable>
                <resource name="hrm_skill_type">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$SkillType"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="$SkillType"/></data>
                </resource>

                <!-- HRM Skill -->
                <resource name="hrm_competency_rating">
                    <reference field="skill_type_id" resource="hrm_skill_type">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$SkillType"/>
                        </xsl:attribute>
                    </reference>
                    <data field="name"><xsl:value-of select="col[@field='name']"/></data>
                    <data field="priority"><xsl:value-of select="col[@field='priority']"/></data>
	            </resource>
            </xsl:for-each>
        </s3xml>
    </xsl:template>
</xsl:stylesheet>
