// =====================================================================
// rs-init.js — khởi tạo MongoDB Replica Set (chạy bằng mongosh bên trong mongo1)
// Idempotent: chạy lại nhiều lần không sao. Đọc IP từ biến môi trường.
//   docker exec -e MONGO_RS=rs0 -e MONGO1_IP=... mongo1 mongosh --quiet /lab-scripts/rs-init.js
// =====================================================================
const rsName = process.env.MONGO_RS || "rs0";
const ips = [process.env.MONGO1_IP, process.env.MONGO2_IP, process.env.MONGO3_IP];
if (ips.some((ip) => !ip)) {
  print("Thiếu biến MONGO1_IP/MONGO2_IP/MONGO3_IP");
  quit(2);
}

function alreadyInitialized() {
  try {
    return rs.status().ok === 1;
  } catch (e) {
    // code 94 = NotYetInitialized → chưa khởi tạo
    if (e.code === 94 || /NotYetInitialized|no replset config/i.test(String(e))) {
      return false;
    }
    throw e;
  }
}

if (!alreadyInitialized()) {
  // Mọi member cùng priority 1 → không có "priority takeover" sau khi hết sự cố,
  // giúp thí nghiệm rollback (E6) dễ diễn giải hơn.
  const cfg = {
    _id: rsName,
    members: ips.map((ip, i) => ({ _id: i, host: `${ip}:27017`, priority: 1 })),
  };
  print("Khởi tạo replica set: " + JSON.stringify(cfg));
  printjson(rs.initiate(cfg));
} else {
  print("Replica set đã được khởi tạo từ trước — bỏ qua rs.initiate()");
}

// Chờ có PRIMARY (tối đa 90 giây)
for (let i = 0; i < 90; i++) {
  try {
    const st = rs.status();
    const primary = st.members.find((m) => m.stateStr === "PRIMARY");
    if (primary) {
      print("PRIMARY hiện tại: " + primary.name);
      st.members.forEach((m) => print(`  ${m.name}  ${m.stateStr}`));
      quit(0);
    }
  } catch (e) {
    // replica set đang bầu chọn, thử lại
  }
  sleep(1000);
}
print("Sau 90 giây vẫn chưa có PRIMARY");
quit(1);
