with
	LOV as (
		select L.LOV_NAME, LD.DISPLAY_VALUE, LD.RETURN_VALUE
		from APP_LIST_OF_VALUES_DTL LD
		inner join APP_LIST_OF_VALUES L
			on LD.LOV_ID = L.LOV_ID
	)
select I.INVOICE_ID, I.INVOICE_DATE,  
       S.SUPPLIER_ID,
	   S.PHONE as SUP_PHONE,
       ST.STORE_NAME,
       
       case when I.INVOICE_TYPE between 11 and 19 then ' رقم العميل '
            when I.INVOICE_TYPE between  21 and  29  then 'رقم المورد '
       end SUPPLIER_LABEL_NO,
	    case when I.INVOICE_TYPE between 11 and 19 then ' العميل '
            when I.INVOICE_TYPE between  21 and  29  then 'المورد '
       end SUPPLIER_LABEL,
       case when I.INVOICE_TYPE between 11 and 19 then S.VAT_NO
       end VAT_NO,
        
       case when I.INVOICE_TYPE between 11 and 19 then S.ADDRESS
       end ADDRESS,
       
        LOV1.DISPLAY_VALUE as CASH_TYPE_NAME,
       
       
       case when I.CASH_TYPE = 1 then 'الصندوق  '
            when  I.CASH_TYPE in (3, 4) then 'البنك  '
       end BOX_LABLE,
       
       case when I.INVOICE_TYPE between 11 and 19 then 'العميل  '
            when I.INVOICE_TYPE between 21 and 29  then 'المستلم '
       end SUP_NAME_L,
       
       case when I.CASH_TYPE = 1 then (select BOX_NAME
				  from $P!{P_SCHEMA_NAME}.BOX 
				  where BOX_ID = I.BOX_NO)
            when I.CASH_TYPE in(3, 4) then (select BANK_NAME
				  from $P!{P_SCHEMA_NAME}.BANK
				  where BANK_ID = I.BOX_NO)                  
                                      
       end BOX_NAME,
       
       case when I.INVOICE_TYPE between 11 and 19 then (select VAT_NO
					from $P!{P_SCHEMA_NAME}.COMPANY_INFO
					where COMPANY_NO = I.COMPANY_NO )
       end VAT_COMP_NO,
	   SR.SR_NAME_AR  as SR_NAME,
      
       to_char(I.INVOICE_TIME, 'YYYY-MM-DD  hh:mi:ss ') as INVOICE_TIME,
	    KSA_E_INVOICING_PKG.GET_BASE64_QRCODE_FOR_INVOICE($P{P_SCHEMA_NAME}, $P{P_INVOICE_ID}, $P{P_INVOICE_TYPE},   CI.MAIN_COMPANY_ID ) as QRCODE,
		case 
			when I.INVOICE_TYPE between 11 and 19 then
				 S_DATA.SUPPLIER_ID
			when I.INVOICE_TYPE between 21 and  29 then
				 C_DATA.COMPANY_NO
		end as CUST_ID,
		case 
			when I.INVOICE_TYPE between 11 and 19 then
				 S_DATA.SUPPLIER_NAME
			when I.INVOICE_TYPE between 21 and  29 then
				 C_DATA.COMPANY_NAME
		end as CUST_NAME,
		case 
			when I.INVOICE_TYPE between 11 and 19 then
				 S_DATA.VAT_NO
			when I.INVOICE_TYPE between 21 and  29 then
				 C_DATA.VAT_NO
		end as CUST_VAT_NO,
		case 
			when I.INVOICE_TYPE between 11 and 19 then
				 S_DATA.STREET_NAME
			when I.INVOICE_TYPE between 21 and  29 then
				 C_DATA.STREET_NAME
		end as CUST_STREET_NAME,
		case 
			when I.INVOICE_TYPE between 11 and 19 then
				 S_DATA.BUILDING_NO
			when I.INVOICE_TYPE between 21 and  29 then
				 C_DATA.BUILDING_NO
		end as CUST_BUILDING_NO,
		case 
			when I.INVOICE_TYPE between 11 and 19 then
				 S_DATA.DISTRICT_NAME
			when I.INVOICE_TYPE between 21 and  29 then
				 C_DATA.DISTRICT_NAME
		end as CUST_DISTRICT_NAME,
		case 
			when I.INVOICE_TYPE between 11 and 19 then
				 S_DATA.CITY_NAME
			when I.INVOICE_TYPE between 21 and  29 then
				 C_DATA.CITY_NAME
		end as CUST_CITY_NAME,
		case 
			when I.INVOICE_TYPE between 11 and 19 then
				 S_DATA.ZIP_CODE
			when I.INVOICE_TYPE between 21 and  29 then
				 C_DATA.ZIP_CODE
		end as CUST_ZIP_CODE,
		case 
			when I.INVOICE_TYPE between 11 and 19 then
				 S_DATA.IDENTIFICATION_CODE
			when I.INVOICE_TYPE between 21 and  29 then
				 C_DATA.IDENTIFICATION_CODE
		end as CUST_IDENTIFICATION_CODE,
		case 
			when I.INVOICE_TYPE between 11 and 19 then
				 S_DATA.SHORT_ADDRESS
			when I.INVOICE_TYPE between 21 and  29 then
				 ''
		end as CUST_SHORT_ADDRESS,
		case 
			when I.INVOICE_TYPE between 11 and 19 then
				 S_DATA.ADDITIONAL_NO
			when I.INVOICE_TYPE between 21 and  29 then
				 ''
		end as CUST_ADDITIONAL_NO,
		case 
			when I.INVOICE_TYPE between 11 and 19 then
				 S_DATA.UNIT_NO
			when I.INVOICE_TYPE between 21 and  29 then
				 ''
		end as CUST_UNIT_NO,
		case 
			when I.INVOICE_TYPE between 11 and 19 then
				S_DATA.COMMERCE_REGISTER
			when I.INVOICE_TYPE between 21 and  29 then
				 C_DATA.COMMERCE_REGISTER
		end as CUST_COMMERCE_REGISTER,
		-------------------------------------------------------------------------------
		case 
			when I.INVOICE_TYPE between 11 and 19 then
				 C_DATA.COMPANY_NO
			when I.INVOICE_TYPE between 21 and  29 then
				 S_DATA.SUPPLIER_ID 
		end as SUP_ID,
		case 
			when I.INVOICE_TYPE between 11 and 19 then
				 C_DATA.COMPANY_NAME
				
			when I.INVOICE_TYPE between 21 and  29 then
				 S_DATA.SUPPLIER_NAME
		end as SUP_NAME,
		case 
			when I.INVOICE_TYPE between 11 and 19 then
				 C_DATA.VAT_NO
			when I.INVOICE_TYPE between 21 and  29 then
				 S_DATA.VAT_NO
		end as SUP_VAT_NO,
		case 
			when I.INVOICE_TYPE between 11 and 19 then
				 C_DATA.STREET_NAME
			when I.INVOICE_TYPE between 21 and  29 then
				 S_DATA.STREET_NAME
		end as SUP_STREET_NAME,
		case 
			when I.INVOICE_TYPE between 11 and 19 then
				 C_DATA.BUILDING_NO
			when I.INVOICE_TYPE between 21 and  29 then
				 S_DATA.BUILDING_NO
		end as SUP_BUILDING_NO,
		case 
			when I.INVOICE_TYPE between 11 and 19 then
				 C_DATA.DISTRICT_NAME
			when I.INVOICE_TYPE between 21 and  29 then
				 S_DATA.DISTRICT_NAME
		end as SUP_DISTRICT_NAME,
		case 
			when I.INVOICE_TYPE between 11 and 19 then
				 C_DATA.CITY_NAME
			when I.INVOICE_TYPE between 21 and  29 then
				 S_DATA.CITY_NAME
		end as SUP_CITY_NAME,
		case 
			when I.INVOICE_TYPE between 11 and 19 then
				 C_DATA.ZIP_CODE
			when I.INVOICE_TYPE between 21 and  29 then
				 S_DATA.ZIP_CODE
		end as SUP_ZIP_CODE,
		case 
			when I.INVOICE_TYPE between 11 and 19 then
				 C_DATA.IDENTIFICATION_CODE
			when I.INVOICE_TYPE between 21 and  29 then
				 S_DATA.IDENTIFICATION_CODE
		end as SUP_IDENTIFICATION_CODE,
		case 
			when I.INVOICE_TYPE between 11 and 19 then
				 ''
			when I.INVOICE_TYPE between 21 and  29 then
				 S_DATA.SHORT_ADDRESS
		end as SUP_SHORT_ADDRESS,
		case 
			when I.INVOICE_TYPE between 11 and 19 then
				 ''
			when I.INVOICE_TYPE between 21 and  29 then
				 S_DATA.ADDITIONAL_NO
		end as SUP_ADDITIONAL_NO,
		case 
			when I.INVOICE_TYPE between 11 and 19 then
				 ''
			when I.INVOICE_TYPE between 21 and  29 then
				 S_DATA.UNIT_NO
		end as SUP_UNIT_NO,
		case 
			when I.INVOICE_TYPE between 11 and 19 then
				 C_DATA.COMMERCE_REGISTER
			when I.INVOICE_TYPE between 21 and  29 then
				 S_DATA.COMMERCE_REGISTER
		end as SUP_COMMERCE_REGISTER,
		
		case when I.INVOICE_TYPE in (21, 23) then
			'Y'
		else
			'N'
		end as SHOW_INV_MANUALLY,
		I.INV_MANUALLY
   
	                                              
from $P!{P_SCHEMA_NAME}.INVOICE I
inner join $P!{P_SCHEMA_NAME}.SUPPLIER S
	on S.SUPPLIER_ID = I.ACCOUNT_NO_DTL
	and S.TYPE = case when I.INVOICE_TYPE between 11 and 19 then 2
                      when I.INVOICE_TYPE between 21 and  29 then 1
                 end
	and I.INVOICE_ID = $P{P_INVOICE_ID}
    and I.INVOICE_TYPE = $P{P_INVOICE_TYPE}
inner join $P!{P_SCHEMA_NAME}.STORE ST
	on I.STORE_NO = ST.STORE_ID
left join $P!{P_SCHEMA_NAME}.COMPANY_INFO CI
	on I.COMPANY_NO = CI.COMPANY_NO
left join $P!{P_SCHEMA_NAME}.SALES_REPRESENTATIVE SR
	on SR.SR_ID = I.SR_NO
	and SR_TYPE = 1
	---
inner join (
			select
				S.SUPPLIER_ID,
				S.SUPPLIER_NAME,
				S.VAT_NO,
				S.COMMERCE_REGISTER,
				S.TYPE,
				KNA.STREET_NAME,
				KNA.BUILDING_NO,
				KNA.DISTRICT_NAME,
				KNA.CITY_NAME,
				KNA.ZIP_CODE,
				KNA.SHORT_ADDRESS,
				KNA.ADDITIONAL_NO,
				KNA.UNIT_NO,
				'SA' as IDENTIFICATION_CODE
			from $P!{P_SCHEMA_NAME}.SUPPLIER S
			left join $P!{P_SCHEMA_NAME}.KSA_NATIONAL_ADDRESS KNA
				on S.NATIONAL_ADDRESS_ID = KNA.ID
			
		) S_DATA
			on I.ACCOUNT_NO_DTL = S_DATA.SUPPLIER_ID
			and S_DATA.TYPE = case when I.INVOICE_TYPE between 11 and 19 then 2
										  when I.INVOICE_TYPE between 21 and  29 then 1
								   end

inner join (
		select 
			CI.COMPANY_NO, 
			MC.COMPANY_NAME, 
			MC.VAT_NO,
			MC.COMMERCE_REGISTER,
			KNA.STREET_NAME,
			KNA.BUILDING_NO,
			KNA.DISTRICT_NAME,
			KNA.CITY_NAME,
			KNA.ZIP_CODE,
			'SA' AS IDENTIFICATION_CODE
		from $P!{P_SCHEMA_NAME}.COMPANY_INFO CI
		inner join $P!{P_SCHEMA_NAME}.COMPANY_INFO MC
			on CI.MAIN_COMPANY_ID = MC.COMPANY_NO
			and MC.COMPANY_TYPE = 2
		left join $P!{P_SCHEMA_NAME}.KSA_NATIONAL_ADDRESS KNA
			on MC.NATIONAL_ADDRESS_ID = KNA.ID
) C_DATA
	on I.COMPANY_NO = C_DATA.COMPANY_NO
and I.INVOICE_ID = $P{P_INVOICE_ID}
and I.INVOICE_TYPE = $P{P_INVOICE_TYPE}

left join LOV LOV1
		on LOV1.LOV_NAME = 'CASH TYPES'
	    and LOV1.RETURN_VALUE = to_char(I.CASH_TYPE)