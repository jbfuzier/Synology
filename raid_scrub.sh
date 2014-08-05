RAID_ARRAY="md3"
MAIL_TO=someone@XXXX.fr
BASE_RAID_ARRAY_DIR="/sys/block/${RAID_ARRAY}/md"

echo $BASE_RAID_ARRAY_DIR

RAID_ACTION_STATUS=`cat ${BASE_RAID_ARRAY_DIR}/sync_action`

echo "raid current action : $RAID_ACTION_STATUS"


echo check > $BASE_RAID_ARRAY_DIR/sync_action
sleep 10
RAID_ACTION_STATUS=`cat ${BASE_RAID_ARRAY_DIR}/sync_action`
while [ "$RAID_ACTION_STATUS" = "check" ]
do
echo "Still check"
sleep 3600
RAID_ACTION_STATUS=`cat ${BASE_RAID_ARRAY_DIR}/sync_action`
done




echo "Scrubbing Done"

RAID_MISMATCH_CNT=`cat ${BASE_RAID_ARRAY_DIR}/mismatch_cnt`

HDD_HAS_ERRORS=`cat /sys/block/${RAID_ARRAY}/md/rd*/errors|grep -v 0|wc -l`

echo "mismatch count : $RAID_MISMATCH_CNT"
if [ $RAID_MISMATCH_CNT == "0" ]
then
echo "Integrity is ok"
echo "Scrubbing done, raid integrity is ok : ${RAID_MISMATCH_CNT}" |/opt/bin/nail -s "OK : RAID PARITY CHECK SUCCESS" $MAIL_TO
else
echo "Intergrity is ko"
echo "Integrity error detected on raid ${RAID_ARRAY} while scrubbing : ${RAID_MISMATCH_CNT}"|/opt/bin/nail -s "CRITICAL : RAID PARITY ERROR" $MAIL_TO
fi

if [ $HDD_HAS_ERRORS != "0" ]
then
echo "Errors on HDD"
echo "CRITICAL : ERRORS ON RAID HDD"|/opt/bin/nail -s "CRITICAL :  ERRORS ON RAID HDD" $MAIL_TO
else
echo "No error on HDD"
fi

