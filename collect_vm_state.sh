#!/bin/bash
function print_info_each_cpu {
        COMMAND=$1
        for i in `seq 0 $LAST_CPU_ID`; do
                echo "CPU #"${i}":"
                virsh qemu-monitor-command $VM_NAME \
                        '{ "execute": "human-monitor-command", ' \
                        '"arguments": {' \
                                '"cpu-index":'${i}','\
                                '"command-line": "info '${COMMAND}'" } }' \
                        | sed 's/\\r\\n/\n/g' | sed 's/\\t/\t/g'
        done
}

function print_header {
        HEADER=$1
        HEADER=`echo $1 | tr '[:lower:]' '[:upper:]'`
        echo  "===== ${HEADER} STATE ====="
}

function print_info {
        COMMAND=$1
        print_header $COMMAND
        virsh qemu-monitor-command $VM_NAME --hmp info $COMMAND
}


VM_NAME=$1

if [[ -z $VM_NAME ]]; then
        echo "Collect information about VM via qemu-monitor interface"
        echo "Usage:$0 <vm_name>"
        exit
fi

CPUS=`virsh qemu-monitor-command $VM_NAME --hmp info cpus | wc -l`
CPUS=$((CPUS-2))
LAST_CPU_ID=$((CPUS-1))

echo "$VM_NAME cpu number: $CPUS"

print_info "cpus"

for INFO_TYPE in "registers" "lapic"; do
        print_header $INFO_TYPE
        print_info_each_cpu $INFO_TYPE
done

print_info "ioapic"
