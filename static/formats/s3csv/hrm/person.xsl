<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Human Resources - CSV Import Stylesheet

         2011-04-18 / Dominic König <dominic AT aidiq DOT com>

         - use for import to hrm/person resource
         - example raw URL usage:
           Let URLpath be the URL to Sahana Eden appliation
           Let Resource be hrm/person/create
           Let Type be s3csv
           Let CSVPath be the path on the server to the CSV file to be imported
           Let XSLPath be the path on the server to the XSL transform file
           Then in the browser type:
           
           URLpath/Resource.Type?filename=CSVPath&transform=XSLPath
           
           You can add a third argument &ignore_errors
         CSV fields:
         Type............................hrm_human_resource.type
         Sex.............................pr_person.gender (accepting "Mr." or "Ms.")
         First Name......................pr_person.first_name
         Last Name.......................pr_person.last_name
         Title...........................hrm_human_resource.job_title
         Email...........................pr_contact
         Mobile Phone....................pr_contact
         Organisation....................org_organisation
         Acronym.........................org_organisation
         Office Phone....................pr_contact
         Skype...........................pr_contact
         Office..........................org_office.name
         Department......................unused
         Country.........................unused
         Office City.....................gis_location.addr_street
         Office Street address...........gis_location.addr_street
         Office Post code................gis_location.addr_postcode
         Office Lat......................gis_location.lat
         Office Lon......................gis_location.lon
         Exact Coord?....................unused

        creates:
            gis_location.................new, from the given values (no updates!)
            org_office...................linked to that org_organisation and gis_location
            pr_person....................new, from the given values (no updates!)
            pr_contact...................new, linked to that person (no updates!)
            hrm_human_resource...........new, linked to that org_organisation, pr_person and org_office

        @todo:

            - fix location hierarchy (use country name in location_onaccept to match L0?)
            - make updateable (don't use temporary UIDs)

    *********************************************************************** -->

    <xsl:output method="xml"/>
    <xsl:key name="orgs" match="row" use="col[@field='Organisation']"/>
    <xsl:key name="offices" match="row" use="col[@field='Office']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- ********************************************************** -->
            <!-- Create the Organisation -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('orgs', col[@field='Organisation'])[1])]">
                <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>
                <resource name="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$OrgName"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="$OrgName"/></data>
                    <xsl:choose>
                        <xsl:when test="col[@field='Acronym']!=''">
                            <data field="acronym"><xsl:value-of select="col[@field='Acronym']"/></data>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:variable name="OrgAcronymTemp"  select="substring-after(col[@field='Email'],'@')"/>
                            <xsl:variable name="OrgAcronym"  select="substring-before($OrgAcronymTemp,'.')"/>
                            <data field="acronym"><xsl:value-of select="$OrgAcronym"/></data>
                        </xsl:otherwise>
                    </xsl:choose>
                </resource>

                <!-- ****************************************************** -->
                <!-- Create the Offices under the organisation -->
                <xsl:for-each select="key('orgs', col[@field='Organisation'])">
                    <xsl:variable name="OfficeName" select="col[@field='Office']/text()"/>
                    <resource name="org_office">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$OfficeName"/>
                        </xsl:attribute>
                        <!-- Office Data -->
                        <data field="name"><xsl:value-of select="$OfficeName"/></data>
                        <!-- Link to Organisation -->
                        <reference field="organisation_id" resource="org_organisation">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$OrgName"/>
                            </xsl:attribute>
                        </reference>
                        <!-- In-line Location Reference -->
                        <reference field="location_id" resource="gis_location">
                            <resource name="gis_location">
                                <data field="name"><xsl:value-of select="$OfficeName"/></data>
                                <data field="lat"><xsl:value-of select="col[@field='Office Lat']"/></data>
                                <data field="lon"><xsl:value-of select="col[@field='Office Lon']"/></data>
                                <data field="addr_street">
                                    <xsl:value-of select="concat(
                                                            col[@field='Office Street address'], ', ',
                                                            col[@field='Office City'])"/>
                                </data>
                                <data field="addr_postcode">
                                    <xsl:value-of select="col[@field='Office Post code']"/>
                                </data>
                            </resource>
                        </reference>
                    </resource>

                    <!-- ****************************************************** -->
                    <!-- Add staff records to the office -->
                        <resource name="pr_person">

                            <!-- Person record -->
                            <data field="first_name"><xsl:value-of select="col[@field='First Name']"/></data>
                            <data field="last_name"><xsl:value-of select="col[@field='Last Name']"/></data>
                            <data field="gender">
                                <xsl:attribute name="value">
                                    <xsl:choose>
                                        <xsl:when test="col[@field='Sex']/text()='Mr.'">3</xsl:when>
                                        <xsl:when test="col[@field='Sex']/text()='Ms.'">2</xsl:when>
                                        <xsl:otherwise>1</xsl:otherwise>
                                    </xsl:choose>
                                </xsl:attribute>
                            </data>

                            <!-- Contact Information -->
                            <xsl:if test="col[@field='Email']!=''">
                                <resource name="pr_contact">
                                    <data field="contact_method" value="EMAIL"/>
                                    <data field="value"><xsl:value-of select="col[@field='Email']/text()"/></data>
                                </resource>
                            </xsl:if>
                            <xsl:if test="col[@field='Mobile Phone']!=''">
                                <resource name="pr_contact">
                                    <data field="contact_method" value="SMS"/>
                                    <data field="value"><xsl:value-of select="col[@field='Mobile Phone']/text()"/></data>
                                </resource>
                            </xsl:if>
                            <xsl:if test="col[@field='Office Phone']!=''">
                                <resource name="pr_contact">
                                    <data field="contact_method" value="WORK_PHONE"/>
                                    <data field="value"><xsl:value-of select="col[@field='Office Phone']/text()"/></data>
                                </resource>
                            </xsl:if>
                            <xsl:if test="col[@field='Skype']!=''">
                                <resource name="pr_contact">
                                    <data field="contact_method" value="SKYPE"/>
                                    <data field="value"><xsl:value-of select="col[@field='Skype']/text()"/></data>
                                </resource>
                            </xsl:if>

                            <!-- HR record -->
                            <resource name="hrm_human_resource">
                                <!-- Link to Organisation -->
                                <reference field="organisation_id" resource="org_organisation">
                                    <xsl:attribute name="tuid">
                                        <xsl:value-of select="$OrgName"/>
                                    </xsl:attribute>
                                </reference>
                                <!-- Link to Site -->
                                <reference field="site_id" resource="org_office">
                                    <xsl:attribute name="tuid">
                                        <xsl:value-of select="$OfficeName"/>
                                    </xsl:attribute>
                                </reference>
                                <!-- Data -->
                                <xsl:choose>
                                    <xsl:when test="col[@field='Type']='Staff'">
                                        <data field="type" value="1"/><!-- Staff -->
                                    </xsl:when>
                                    <xsl:when test="col[@field='Type']='Volunteer'">
                                        <data field="type" value="2"/> <!-- Volunteer -->
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <data field="type" value="1"/> <!-- Staff -->
                                    </xsl:otherwise>
                                </xsl:choose>
                                <data field="job_title">
                                    <xsl:value-of select="col[@field='Title']"/>
                                </data>
                            </resource>

                        </resource>

                </xsl:for-each>

            </xsl:for-each>
        </s3xml>
    </xsl:template>
</xsl:stylesheet>
