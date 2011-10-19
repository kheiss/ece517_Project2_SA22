<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Organisation - CSV Import Stylesheet

         2011-Jun-13 / Graeme Foster <graeme AT acm DOT org>

         - use for import to auth/user resource
         - example raw URL usage:
           Let URLpath be the URL to Sahana Eden appliation
           Let Resource be org/organisation/create
           Let Type be s3csv
           Let CSVPath be the path on the server to the CSV file to be imported
           Let XSLPath be the path on the server to the XSL transform file
           Then in the browser type:
           
           URLpath/Resource.Type?filename=CSVPath&transform=XSLPath
           
           You can add a third argument &ignore_errors

         CSV fields:
         first_name..............auth_user
         last_name...............auth_user
         email...................auth_user
         password................auth_user
         role....................auth_role
         organisation............org_organisation

    *********************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- ********************************************************** -->
            <!-- Create each record -->
            <xsl:for-each select="table/row">
                <!-- Lookup table Organisation -->
                <resource name="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="col[@field='organisation']"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="col[@field='organisation']"/></data>
                </resource>
                <!-- Create the User -->
                <resource name="auth_user">
                    <data field="first_name"><xsl:value-of select="col[@field='first_name']"/></data>
                    <data field="last_name"><xsl:value-of select="col[@field='last_name']"/></data>
                    <data field="email"><xsl:value-of select="col[@field='email']"/></data>
                    <data field="password">
                        <xsl:attribute name="value">
                            <xsl:value-of select="col[@field='password']"/>
                        </xsl:attribute>
                    </data>
                    <!-- Every user must have the authenticated role -->
                    <resource name="auth_membership">
                        <reference field="group_id" resource="auth_group" uuid="AUTHENTICATED"/>
                    </resource>
                    <!-- Add other roles as per list -->
                    <xsl:call-template name="roles">
                        <xsl:with-param name="uids" select="col[@field='role']/text()"/>
                    </xsl:call-template>
                    <!-- Link to Organisation -->
                    <reference field="organisation_id" resource="org_organisation">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="col[@field='organisation']"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:for-each>
        </s3xml>
    </xsl:template>

    <xsl:template name="roles">
        <xsl:param name="uids"/>
        <xsl:choose>
            <xsl:when test="contains(uids, ',')">
                <xsl:variable name="uid">
                    <xsl:value-of select="substring-before(uids, ',')"/>
                </xsl:variable>
                <xsl:variable name="rest">
                    <xsl:value-of select="substring-after(uids, ',')"/>
                </xsl:variable>
                <xsl:call-template name="membership">
                    <xsl:with-param name="uid" select="$uid"/>
                </xsl:call-template>
                <xsl:call-template name="roles">
                    <xsl:with-param name="uids" select="$rest"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="membership">
                    <xsl:with-param name="uid" select="$uids"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template name="membership">
        <xsl:param name="uid"/>

        <xsl:variable name="nuid">
            <xsl:value-of select="normalize-space($uid)"/>
        </xsl:variable>

        <xsl:if test="$nuid!=''">
            <resource name="auth_membership">
                <reference field="group_id" resource="auth_group">
                    <xsl:attribute name="uuid">
                        <xsl:value-of select="$uid"/>
                    </xsl:attribute>
                </reference>
            </resource>
        </xsl:if>
    </xsl:template>

</xsl:stylesheet>
