<script setup>
import { ref, reactive, watch, watchEffect, toValue, toRef, onMounted } from 'vue'
const service = ref({})
// const track_number = ref({})
const serviceUnchanged = ref(true)

// const newTrackNumber = ref(null)
// const newTrackCompany = ref('cjkorex')
// const newTrackRemark = ref('')

// const base_url = 'http://lzh1.ddns.net/settings/'
// const base_url = './'
const base_url = ''

onMounted(() => {
    updateDb(base_url + 'service-update', {}, service)
    // updateDb(base_url + 'track-number-update', {}, track_number)
})

async function restoreService() {
    serviceUnchanged.value = true
    const { data, error } = await updateDb(base_url + 'service-update', {}, service)
    if (error) { serviceUnchanged.value = false }
}
async function saveService() {
    serviceUnchanged.value = true
    const { data, error } = await updateDb(base_url + 'service-update', service.value)
    if (error) { serviceUnchanged.value = false }
}


function isActiveOnClick(value) {
    value.isActive = !value.isActive
    serviceUnchanged.value = false
}
function serviceChanged() {
    serviceUnchanged.value = false
}
// function deleteTrackNumber(key) {
//     updateDb(base_url + 'track-number-delete', { [key]: {} }, track_number)
// }

// function addTrackNumber() {
//     if (newTrackNumber.value === null) return
//     updateDb(base_url + 'track-number-update', { [newTrackNumber.value]: { company: newTrackCompany.value, remark: newTrackRemark.value } }, track_number)
//     newTrackNumber.value = null
//     newTrackCompany.value = 'cjkorex'
//     newTrackRemark.value = ''
// }
async function updateDb(url, jsonGo, refSave = null) {
    let jsonCome = null;
    let errorCome = null;
    try {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(jsonGo)
        })
        jsonCome = await res.json()
    } catch (e) {
        errorCome = e
    }
    console.log(jsonCome)
    if (!refSave || errorCome || jsonCome.type != 'success') {
    } else {
        refSave.value = jsonCome.data
    }
    return { jsonCome, errorCome }
}
</script>




<template>

    <table>
        <thead>
            <tr>
                <th>Name</th>
                <th>isActive</th>
                <th>qpd-min</th>
                <th>qpd-max</th>
            </tr>
        </thead>
        <tr v-for="(value, name) in service" :key="name">
            <td>{{ name }}</td>
            <td><button @click="isActiveOnClick(value)">{{ value.isActive }}</button></td>
            <td><input class="serviceQpd" type="number" min="1" max="999999" step="1" inputmode="numeric" v-model="value.qpd[0]" @input="serviceChanged()"></td>
            <td><input class=" serviceQpd" type="number" min="1" max="999999" step="1" inputmode="numeric" v-model="value.qpd[1]" @input="serviceChanged()"></td>
        </tr>
        <tfoot></tfoot>
    </table>
    <div>
        <button :disabled="serviceUnchanged" @click="restoreService()">Cancel</button>
        <button :disabled="serviceUnchanged" @click="saveService()">Save</button>
    </div>

    <!-- 
    <TransitionGroup name="list" tag="table" v-if="service.shiptrack.isActive">
        <thead>
            <tr>
                <th>Number</th>
                <th>Company</th>
                <th>Remark</th>
                <th></th>
            </tr>
        </thead>
        <tr v-for="(data, key) in track_number" :key="key">
            <td style="user-select: all;"><a :href="`https://track.shiptrack.co.kr/${data.company}/${key}`" target="_blank" rel="noopener noreferrer">{{ key }}</a></td>
            <td>{{ data.company }}</td>
            <td>{{ data.remark }}</td>
            <td><button class="trackBtn" @click="deleteTrackNumber(key)">-</button></td>
        </tr>
        <tr>
            <td><input type="text" style="width: 8em;" v-model="newTrackNumber"></td>
            <td><select style="width: 6em;" v-model="newTrackCompany">
                    <option>cjkorex</option>
                    <option>hanjin</option>
                </select></td>
            <td><input type="text" style="width: 6em;" v-model="newTrackRemark"></td>
            <td><button class="trackBtn" @click="addTrackNumber()">+</button></td>
        </tr>
        <tfoot></tfoot>
    </TransitionGroup> 
-->


</template>

<style scoped>
table {
    width: 400px;
    text-align: center;
    border: solid gray 1px;
    border-radius: 10px;
    padding: 10px;
    margin: 20px;
    border-collapse: separate;
    border-spacing: 0px;

}

th,
td {
    padding: 5px 10px;
}

th {
    border-bottom: solid gray 1px;
    padding-bottom: 10px;
    font-weight: 700;
}

button {
    user-select: none !important;
    cursor: pointer;
    width: 4em;
}

button.trackBtn {
    width: 2em;
}

input.serviceQpd {
    width: 5em;
}



.list-move,
/* 对移动中的元素应用的过渡 */
.list-enter-active,
.list-leave-active {
    transition: all 0.2s ease;
}

.list-enter-from,
.list-leave-to {
    opacity: 0;
    transform: translateX(-100px);
}

/* 确保将离开的元素从布局流中删除
  以便能够正确地计算移动的动画。 */
.list-leave-active {
    position: absolute;
}
</style>
