<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Assets - CSV Import Stylesheet

         2011-06-20 / Michael Howden <michael AT aidiq DOT com>

         - use for import to asset/asset resource
         - example raw URL usage:
           Let URLpath be the URL to Sahana Eden appliation
           Let Resource be asset/asset/create
           Let Type be s3csv
           Let CSVPath be the path on the server to the CSV file to be imported
           Let XSLPath be the path on the server to the XSL transform file
           Then in the browser type:
           
           URLpath/Resource.Type?filename=CSVPath&transform=XSLPath
           
           You can add a third argument &ignore_errors
         CSV fields:
         id..............................used for tuid
         Organisation....................asset_log.organisation_id.name
         Acronym.........................asset_log.organisation_id.acronym
         Office..........................asset_log.site_id
         Code............................asset_log.site_id.code
         Catalog.........................supply_catalog_item.catalog_id
         Asset No........................number
         Type............................type
         Category........................supply_catalog_item.item_category_id
         Name............................supply_item.name
         Location........................asset_log.room_id
         Assigned To.....................pr_person.first_name
         Brand...........................supply_brand.brand_id
         Model...........................supply_item.model
         SN..............................sn
         Supplier........................supplier
         Date............................purchase_date
         Price...........................purchase_price
         Comments........................comments

        creates:
            supply_brand.................
            org_office...................
            org_organisation.............
            gis_location.................
            supply_catalog...............
            supply_item_category.........
            supply_item..................
            supply_catalog_item..........
            asset_log....................
            pr_person....................
            org_room.....................
            
        @todo:

            - remove id column

    *********************************************************************** -->

    <xsl:output method="xml"/>
    
    <xsl:strip-space elements="col[@field='Brand']" />
	<xsl:key name="brands" match="row" use="normalize-space(col[@field='Brand'])"/>
	<xsl:key name="offices" match="row" use="normalize-space(col[@field='Office'])"/>
    <xsl:key name="categories" match="row" use="col[@field='Category']"/>
    

    <xsl:template match="/">
        <s3xml>
			<xsl:for-each select="//row[generate-id(.)=generate-id(key('brands', normalize-space(col[@field='Brand']))[1])]">
	            <!-- Brand -->
	            <xsl:variable name="BrandName" select="col[@field='Brand']/text()"/>
	            <xsl:if test="$BrandName != ''">
		            <resource name="supply_brand">
		                <xsl:attribute name="tuid">
		                    <xsl:value-of select="$BrandName"/>
		                </xsl:attribute>
		                <!-- Brand Data -->
		                <data field="name"><xsl:value-of select="$BrandName"/></data>
		            </resource>
	            </xsl:if>
            </xsl:for-each>
            
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('offices', normalize-space(col[@field='Office']))[1])]">
			    <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>
			    <xsl:variable name="OrgAcronym" select="col[@field='Acronym']/text()"/>
			    <xsl:variable name="OfficeName" select="col[@field='Office']/text()"/>
			    <xsl:variable name="CatalogName" select="col[@field='Catalog']/text()"/>
			    
	            <resource name="org_office">
	                <xsl:attribute name="tuid">
	                    <xsl:value-of select="$OfficeName"/>
	                </xsl:attribute>
	                <data field="name"><xsl:value-of select="$OfficeName"/></data>
                    <xsl:if test="col[@field='Code'] != ''">
                        <data field="code"><xsl:value-of select="col[@field='Code']"/></data>
                    </xsl:if>

	                <!-- In-line Organisation -->
	                <reference field="organisation_id" resource="org_organisation">
			            <resource name="org_organisation">
			                <xsl:attribute name="tuid">
			                    <xsl:value-of select="$OrgAcronym"/>
			                </xsl:attribute>
			                <data field="name"><xsl:value-of select="$OrgName"/></data>
			                <data field="acronym"><xsl:value-of select="$OrgAcronym"/></data>
			            </resource>
	                </reference>
	                <!-- In-line Location Reference -->
	                <reference field="location_id" resource="gis_location">
	                    <resource name="gis_location">
	                        <data field="name"><xsl:value-of select="$OfficeName"/></data>
	                    </resource>
	                </reference>
	            </resource>
            
	            <resource name="supply_catalog">
	                <xsl:attribute name="tuid">
	                    <xsl:value-of select="$CatalogName"/>
	                </xsl:attribute>
	                <data field="name"><xsl:value-of select="$CatalogName"/></data>
	            </resource>
            

            
	            <xsl:for-each select="//row[generate-id(.)=generate-id(key('categories', col[@field='Category'])[1])]">
	                <!-- Item Categories -->
	                <xsl:variable name="CategoryName" select="col[@field='Category']/text()"/>
	                <resource name="supply_item_category">
	                    <xsl:attribute name="tuid">
	                        <xsl:value-of select="$CategoryName"/>
	                    </xsl:attribute>
	                    <!-- Item Category Data -->
	                    <data field="name"><xsl:value-of select="$CategoryName"/></data>
	                    <!-- Link to Catalog -->
	                    <reference field="catalog_id" resource="supply_catalog">
	                        <xsl:attribute name="tuid">
	                            <xsl:value-of select="$CatalogName"/>
	                        </xsl:attribute>
	                    </reference>
	                    
	                </resource>
	                
	                <xsl:for-each select="key('categories', col[@field='Category'])">
		                <!-- Item  -->
		                <xsl:variable name="ItemCode" select="concat(
		                                                        col[@field='Name'], ', ',
		                                                        col[@field='Model'], ', ',
		                                                        col[@field='Brand'])"/>
		                <xsl:variable name="Name" select="col[@field='Name']/text()"/>
		                <xsl:variable name="Model" select="col[@field='Model']/text()"/>
	
		                <resource name="supply_item">
		                    <xsl:attribute name="tuid">
		                        <xsl:value-of select="$ItemCode"/>
		                    </xsl:attribute>
		                    <!-- Item Data -->
		                    <data field="name"><xsl:value-of select="$Name"/></data>
		                    <data field="model"><xsl:value-of select="$Model"/></data>
		                    <data field="um">piece</data>
		                    
		                    <!-- Link to Brand -->
		                    <xsl:variable name="BrandName" select="col[@field='Brand']/text()"/>
		                    <xsl:if test="$BrandName != ''">
			                    <reference field="brand_id" resource="supply_brand">
			                        <xsl:attribute name="tuid">
			                            <xsl:value-of select="$BrandName"/>
			                        </xsl:attribute>
			                    </reference>
			                </xsl:if>
			                
			                <!-- Catalog Item Components -->
			                <resource name="supply_catalog_item">
				                <xsl:attribute name="tuid">
			                        <xsl:value-of select="$ItemCode"/>
			                    </xsl:attribute>
			                    <!-- Link to Catalog -->
			                    <reference field="catalog_id" resource="supply_catalog">
			                        <xsl:attribute name="tuid">
			                            <xsl:value-of select="$CatalogName"/>
			                        </xsl:attribute>
			                    </reference>
			                    
			                    <!-- Link to Category -->
			                    <reference field="item_category_id" resource="supply_item_category">
			                        <xsl:attribute name="tuid">
			                            <xsl:value-of select="$CategoryName"/>
			                        </xsl:attribute>
			                    </reference>
			                    <!-- Must include a field (workaround) -->
			                    <data field="comments">_</data>
			                 </resource>
		                </resource>
		                <!-- Person  -->
	                    <xsl:variable name="PersonName" select="col[@field='Assigned To']/text()"/>
	                    <xsl:if test="$PersonName != ''">
	                        <resource name="pr_person">
	                            <xsl:attribute name="tuid">
	                                <xsl:value-of select="$PersonName"/>
	                            </xsl:attribute>
	                            <data field="first_name"><xsl:value-of select="$PersonName"/></data>
	                        </resource>
	                    </xsl:if>
	                    
	                    <!-- Room  -->
	                    <xsl:variable name="RoomName" select="col[@field='Location']/text()"/>
	                    <xsl:if test="$RoomName != ''">
	                        <resource name="org_room">
	                            <xsl:attribute name="tuid">
	                                <xsl:value-of select="$RoomName"/>
	                            </xsl:attribute>
	                            <data field="name"><xsl:value-of select="$RoomName"/></data>
	                            
	                            <!-- Link to Site 
	                            <reference field="site_id" resource="org_site">
	                                <xsl:attribute name="tuid">
	                                    <xsl:value-of select="$OfficeName"/>
	                                </xsl:attribute>
	                            </reference>-->
	                        </resource>
	                    </xsl:if>
	                    
	                    <!-- Asset  -->
	                    <xsl:variable name="ID" select="col[@field='id']/text()"/>
	                    <xsl:variable name="AssetNumber" select="col[@field='Asset No']/text()"/>
	                    <resource name="asset_asset">
	                        <xsl:attribute name="tuid">
	                            <xsl:value-of select="col[@field='id']/text()"/>
	                        </xsl:attribute>
	                        <!-- Asset Data -->
	                        <xsl:if test="$AssetNumber != ''">
	                        	<data field="number"><xsl:value-of select="$AssetNumber"/></data>
	                        </xsl:if>
	                        <xsl:if test="col[@field='SN'] != ''">
	                        	<data field="sn"><xsl:value-of select="col[@field='SN']"/></data>
	                        </xsl:if>
	                        <xsl:if test="col[@field='Type'] != ''">
	                        	<data field="type"><xsl:value-of select="col[@field='Type']"/></data>
	                        </xsl:if>
	                        <xsl:if test="col[@field='Supplier'] != ''">
	                        	<data field="supplier"><xsl:value-of select="col[@field='Supplier']"/></data>
	                        </xsl:if>
	                        <xsl:if test="col[@field='Date'] != ''">
	                        	<data field="purchase_date"><xsl:value-of select="col[@field='Date']"/></data>
	                        </xsl:if>
	                        <xsl:if test="col[@field='Price'] != ''">
	                        	<data field="purchase_price"><xsl:value-of select="col[@field='Price']"/></data>
	                        </xsl:if>
	                        <xsl:if test="col[@field='Comments'] != ''">
	                        	<data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
	                        </xsl:if>
	                        <!-- Link to Item -->
	                        <reference field="item_id" resource="supply_item">
	                            <xsl:attribute name="tuid">
	                                <xsl:value-of select="$ItemCode"/>
	                            </xsl:attribute>
	                        </reference>
	                        
	                        <!-- Reference to Log -->
	                        <resource name="asset_log">
	                            <!-- Item Category Data -->
	                            <data field="status" value="1"/>
	                            <xsl:variable name="Date" select="col[@field='Date']/text()"/>
	                            <xsl:if test="$Date != ''">
	                            	<data field="datetime"><xsl:value-of select="col[@field='Date']"/>T 00:00:00</data>
	                            </xsl:if>
	                            <xsl:if test="$Date = ''">
	                            	<data field="datetime">2000-01-01 T 00:00:00</data>
	                            </xsl:if>
	                            <data field="cond" value="1"/>
	                            <data field="site_or_location" value="1"/>
	                            
	                            <!-- Link to Organisation -->
	                            <reference field="organisation_id" resource="org_organisation">
	                                <xsl:attribute name="tuid">
	                                    <xsl:value-of select="$OrgAcronym"/>
	                                </xsl:attribute>
	                            </reference>
	                            
	                            <!-- Link to Site -->
	                            <reference field="site_id" resource="org_office">
	                                <xsl:attribute name="tuid">
	                                    <xsl:value-of select="$OfficeName"/>
	                                </xsl:attribute>
	                            </reference>
	                            
	                            <!-- Link to Room -->
	                            <xsl:if test="$RoomName != ''">
		                            <reference field="room_id" resource="org_room">
		                                <xsl:attribute name="tuid">
		                                    <xsl:value-of select="$RoomName"/>
		                                </xsl:attribute>
		                            </reference>
	                            </xsl:if>
	                            
	                            <!-- Link to Person -->
	                            <xsl:if test="$PersonName != ''">
		                            <reference field="person_id" resource="pr_person">
		                                <xsl:attribute name="tuid">
		                                    <xsl:value-of select="$PersonName"/>
		                                </xsl:attribute>
		                            </reference>
	                            </xsl:if>
	                        </resource>
	                    </resource>
	                </xsl:for-each>
	            </xsl:for-each>
            </xsl:for-each>
        </s3xml>
    </xsl:template>
</xsl:stylesheet>
