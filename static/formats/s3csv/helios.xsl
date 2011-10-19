<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         HELIOS - CSV Import Stylesheet

         2011-Jul-28 / Fran Boon <fran AT aidiq DOT com>

         - use for import to org/office/inv_item resource
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
         COUNTRY.................org_organisation.location_id
         CODE_SHARE..............inv_inv_item.item_id.item_category_id
         CODE_ORG................inv_inv_item.item_id.code
         ORGANISATION............org_organisation
         DESCRIPTION.............inv_inv_item.item_id.name
         UOM.....................inv_inv_item.item_id.um
         QUANTITY................inv_inv_item.quantity or inv_recv_item.quantity
         STATUS..................inv_item or inv_recv_item (Stock or On Order)
         DATE....................n/a or inv_recv_item.recv_id.eta
         CONTACTS................org_office.comments

    *********************************************************************** -->
    <xsl:include href="../xml/countries.xsl"/>
    <xsl:template match="/">
        <s3xml>
            <!-- ********************************************************** -->
            <!-- Lookup the Item Catalog -->
            <xsl:variable name="ItemCatalog">
                <xsl:text>Interagency Shared Items</xsl:text>
            </xsl:variable>
            <resource name="supply_item_category">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$ItemCatalog"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$ItemCatalog"/></data>
            </resource>

            <!-- Create each record -->
            <xsl:for-each select="table/row">

                <!-- Create the Organisation -->
                <!-- @ToDo: Move this above the for-each since only 1 per CSV -->
                <xsl:variable name="OrgName" select="col[@field='ORGANISATION']/text()"/>
                <resource name="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$OrgName"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="$OrgName"/></data>
                    <!-- International NGO -->
                    <data field="type">3</data>
                </resource>
                
                <!-- Create the Office -->
                <!-- @ToDo: Move this above the for-each since only 1 per CSV -->
                <xsl:variable name="OfficeName">
                    <xsl:value-of select="col[@field='ORGANISATION']"/>
                    <xsl:text> (</xsl:text>
                    <xsl:call-template name="iso2countryname">
                        <xsl:with-param name="country" select="col[@field='COUNTRY']"/>
                    </xsl:call-template>
                    <xsl:text>)</xsl:text>
                </xsl:variable>
                <resource name="org_office">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$OfficeName"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="$OfficeName"/></data>
                    <data field="comments"><xsl:value-of select="col[@field='CONTACTS']"/></data>
                    <!-- Link to Organisation -->
                    <reference field="organisation_id" resource="org_organisation">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$OrgName"/>
                        </xsl:attribute>
                    </reference>
                    <!-- Link to Location -->
                    <reference field="location_id" resource="gis_location">
                        <xsl:attribute name="uuid">
                            <xsl:text>www.sahanafoundation.org/COUNTRY-</xsl:text>
                            <xsl:value-of select="col[@field='COUNTRY']/text()"/>
                        </xsl:attribute>
                    </reference>
                </resource>

                <!-- Create the Item Category -->
                <xsl:variable name="ItemCategory" select="col[@field='CODE_SHARE']/text()"/>
                <resource name="supply_item_category">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$ItemCategory"/>
                    </xsl:attribute>
                    <reference field="catalog_id" resource="supply_catalog">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$ItemCatalog"/>
                        </xsl:attribute>
                    </reference>
                    <data field="name"><xsl:value-of select="$ItemCategory"/></data>
                </resource>

                <!-- Create the Item -->
                <xsl:variable name="ItemCode" select="col[@field='CODE_ORG']/text()"/>
                <resource name="supply_item">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$ItemCode"/>
                    </xsl:attribute>
                    <data field="code"><xsl:value-of select="$ItemCode"/></data>
                    <data field="name"><xsl:value-of select="col[@field='DESCRIPTION']"/></data>
                </resource>

                <!-- Add Item to Catalog -->
                <resource name="supply_catalog_item">
                    <reference field="catalog_id" resource="supply_catalog">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$ItemCatalog"/>
                        </xsl:attribute>
                    </reference>
                    <reference field="item_category_id" resource="supply_item_category">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$ItemCategory"/>
                        </xsl:attribute>
                    </reference>
                    <reference field="item_id" resource="supply_item">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$ItemCode"/>
                        </xsl:attribute>
                    </reference>
                </resource>
                
                <xsl:choose>
                    <xsl:when test="col[@field='STATUS']='Stock'">
                        <!-- Add Item to Inventory -->
                        <resource name="inv_inv_item">
                            <data field="quantity"><xsl:value-of select="col[@field='QUANTITY']"/></data>
                            <reference field="site_id" resource="org_site">
                                <xsl:attribute name="tuid">
                                    <xsl:value-of select="$OfficeName"/>
                                </xsl:attribute>
                            </reference>
                            <!-- @ToDo: How do we fine the auto-created Item Pack? -->
                            <reference field="item_pack_id" resource="supply_item_pack">
                                <xsl:attribute name="tuid">
                                    <xsl:value-of select="$ItemPack"/>
                                </xsl:attribute>
                            </reference>
                        </resource>
                    </xsl:when>
                    <xsl:when test="col[@field='STATUS']='On Order'">
                        <!-- Add Item to Incoming Shipment -->
                        <resource name="inv_recv_item">
                            <data field="quantity"><xsl:value-of select="col[@field='QUANTITY']"/></data>
                            <reference field="recv_id" resource="inv_recv">
                                <data field="eta"><xsl:value-of select="col[@field='DATE']"/></data>
                                <!-- IN_PROCESS -->
                                <data field="status"><xsl:text>0</xsl:text></data>
                                <reference field="site_id" resource="org_site">
                                    <xsl:attribute name="tuid">
                                        <xsl:value-of select="$OfficeName"/>
                                    </xsl:attribute>
                                </reference>
                                <!-- @ToDo: How do we fine the auto-created Item Pack? -->
                                <reference field="item_pack_id" resource="supply_item_pack">
                                    <xsl:attribute name="tuid">
                                        <xsl:value-of select="$ItemPack"/>
                                    </xsl:attribute>
                                </reference>
                            </reference>
                        </resource>
                    </xsl:when>
                    <xsl:when test="col[@field='STATUS']='Planned Purchase'">
                        <!-- @ToDo: Future Iteration -->
                    </xsl:when>
                    <xsl:otherwise>
                        <!-- Error! -->
                    </xsl:otherwise>
                </xsl:choose>

            </xsl:for-each>
        </s3xml>
    </xsl:template>
</xsl:stylesheet>
