// SynthCap シェル（3Dプリント用・2分割）
// 座標系: 原点 = 基板の左下（EXTヘッダー側の辺）、X右、Y上（ジャック側）、Z = 基板裏面が0、表面が +pcb_t
// 基板サイズ・ジャック/エンコーダ/LED/ヘッダーの位置は layout.scad（gen_pcb.py が自動生成）から読む
//
// 出力:
//   openscad -D 'part="base"' -o synthcap_base.stl synthcap_shell.scad   // 裏側（ジャック側）トレー
//   openscad -D 'part="top"'  -o synthcap_top.stl  synthcap_shell.scad   // 表側（ノブ側）カバー
//   part="assembly" で組み立て状態の確認

part = "assembly";

include <layout.scad>   // pcb_w, pcb_h, jack_x, enc_x, enc_y, led_xy, hdr_x0, hdr_x1, ear_x, ear_w, corner_r

// ---------- 基板・部品寸法（実物を測って調整してください） ----------
pcb_t = 1.6;
clr = 0.25;            // 基板とシェルのすき間
wall = 1.6;            // 側壁
floor_t = 1.2;         // 底・天板の厚み

jack_h = 4.5;          // PJ-342 本体の高さ（基板裏面から）
jack_axis = 2.25;      // プラグ軸の高さ（基板裏面から下へ）
jack_hole_d = 6.4;     // 側壁のプラグ穴
jack_over = 1.6;       // ジャックのバレルが基板端からはみ出す長さ（1.4mm + 余裕）
jack_len = 14.0;       // バレル先端から本体後端まで
jack_w = 6.4;
jack_labels = ["MIDI IN", "MIDI OUT", "CLOCK", "OUT1", "OUT2"];

enc_h = 7.0;           // EC12E 本体の高さ（基板表面から、余裕込み）
enc_hole_d = 7.6;      // シャフト穴（軸受けØ7 + 余裕。ノブの径に合わせて）
enc_body = 12.4;       // エンコーダ本体の一辺（干渉確認用）
enc_body_h = 6.5;      // エンコーダ本体の高さ（EC11の値。EC12Eはこれより低い）
led_d = 1.8;           // D1 は裏面。ベース底に導光穴を開ける
hdr_z1 = pcb_t + 5.6;  // EXTヘッダー（L字）の通り穴の高さ

post = 2.4;            // 基板を受ける角の柱

// 上下を留めるツメ（左右の壁に2か所ずつ）。ベースのリップに出っ張り、トップの壁に窓
snap_y = [7, 24];      // ツメの位置（基板下辺から）
snap_len = 6;          // ツメの長さ
snap_p = 0.5;          // 出っ張り量（かかり代は snap_p - 0.15）
snap_z0 = 1.0;         // 出っ張りの下端（= トップ側の帯の高さ）
snap_gap = 0.15;       // リップと受けのすき間

// ---------- 導出値 ----------
ox0 = -clr - wall; oy0 = -clr - wall;
ow = pcb_w + 2 * (clr + wall);
oh = pcb_h + 2 * (clr + wall) + jack_over;
cav_h = pcb_h + 2 * clr + jack_over;     // 内部空間のY方向の長さ
base_z0 = -(jack_h + 0.4) - floor_t;
top_z1 = pcb_t + enc_h + floor_t;
lip_h = 1.4;           // 上下を重ねるリップ

$fn = 48;

module rbox(x, y, z, w, h, d, r = 1.5) {
    translate([x, y, z]) linear_extrude(d)
        offset(r) offset(-r) square([w, h]);
}

// ツメの出っ張り。dir = -1 で左壁（-X向き）、+1 で右壁
module snap_bumps() {
    for (dir = [-1, 1], y = snap_y) {
        xf = (dir < 0) ? ox0 + wall / 2 : ox0 + ow - wall / 2;
        translate([xf, y + snap_len / 2, 0]) rotate([90, 0, 0]) linear_extrude(snap_len)
            polygon([[-dir * 0.3, snap_z0], [0, snap_z0], [dir * snap_p, snap_z0 + snap_p],
                     [dir * snap_p, snap_z0 + snap_p + 0.2], [0, snap_z0 + snap_p + 1.4],
                     [-dir * 0.3, snap_z0 + snap_p + 1.4]]);
    }
}
// ツメが入る窓（トップの壁を貫通）
module snap_windows() {
    w = wall / 2 - snap_gap + 0.2;
    for (y = snap_y) {
        translate([ox0 - 0.1, y - snap_len / 2 - 0.3, snap_z0]) cube([w, snap_len + 0.6, pcb_t + lip_h + 0.2 - snap_z0]);
        translate([ox0 + ow + 0.1 - w, y - snap_len / 2 - 0.3, snap_z0]) cube([w, snap_len + 0.6, pcb_t + lip_h + 0.2 - snap_z0]);
    }
}

module base() {
    difference() {
        union() {
            // 外殻（基板裏面 z=0 まで）
            difference() {
                rbox(ox0, oy0, base_z0, ow, oh, -base_z0);
                rbox(-clr, -clr, base_z0 + floor_t, pcb_w + 2 * clr, cav_h, 50, 0.5);
            }
            // 基板を受ける角の柱（裏面の部品は端から0.3mm以上離れているので、角だけ受ける）
            for (x = [-clr, pcb_w + clr - post], y = [-clr, pcb_h + clr - post])
                translate([x, y, base_z0 + floor_t - 0.01]) cube([post, post, -base_z0 - floor_t + 0.01]);
            // 上カバーにはまるリップ
            difference() {
                rbox(ox0 + wall / 2, oy0 + wall / 2, 0, ow - wall, oh - wall, pcb_t + lip_h, 1.2);
                translate([-clr, -clr, -1]) cube([pcb_w + 2 * clr, cav_h, 10]);
            }
            snap_bumps();
        }
        // ジャックの穴（上辺）
        for (x = jack_x)
            translate([x, pcb_h - 1, -jack_axis]) rotate([-90, 0, 0]) cylinder(d = jack_hole_d, h = 10);
        // EXTヘッダーの通り穴（下辺）
        translate([hdr_x0, -5, -0.5]) cube([hdr_x1 - hdr_x0, 6, hdr_z1 + 1]);
        // LEDの導光穴（底面）
        translate([led_xy[0], led_xy[1], base_z0 - 0.01]) cylinder(d = led_d, h = floor_t + 0.5);
        // 底面の刻印
        translate([pcb_w / 2, pcb_h / 2, base_z0 - 0.01]) mirror([1, 0, 0])
            linear_extrude(0.5) text("SynthCap", size = 6, halign = "center", valign = "center");
    }
}

module top() {
    difference() {
        // 外殻（z=0 から天板まで）
        rbox(ox0, oy0, 0, ow, oh, top_z1);
        // 内部空間
        rbox(-clr, -clr, -1, pcb_w + 2 * clr, cav_h, top_z1 - floor_t + 1, 0.5);
        // ベース側リップの受け
        rbox(ox0 + wall / 2 - 0.15, oy0 + wall / 2 - 0.15, -0.01, ow - wall + 0.3, oh - wall + 0.3, pcb_t + lip_h + 0.2, 1.2);
        snap_windows();
        // ノブの穴
        for (x = enc_x) translate([x, enc_y, 0]) cylinder(d = enc_hole_d, h = 50);
        // ジャック穴（上辺、カバー側の半分）
        for (x = jack_x)
            translate([x, pcb_h - 1, -jack_axis]) rotate([-90, 0, 0]) cylinder(d = jack_hole_d, h = 10);
        // EXTヘッダーの通り穴
        translate([hdr_x0, -5, -0.5]) cube([hdr_x1 - hdr_x0, 6, hdr_z1 + 0.5]);
        // ラベル刻印（天板）
        for (i = [0 : 4])
            translate([jack_x[i], pcb_h - 2.2, top_z1 - 0.5])
                linear_extrude(1) text(jack_labels[i], size = 2.2, halign = "center", valign = "center");
    }
    // 基板を上から押さえる枠（天井から基板の縁まで）
    difference() {
        translate([-clr, -clr, pcb_t]) cube([pcb_w + 2 * clr, pcb_h + 2 * clr, top_z1 - pcb_t - 0.01]);
        translate([0.6, 0.6, 0]) cube([pcb_w - 1.2, pcb_h - 1.2, top_z1 * 2]);
        translate([hdr_x0 - 1, -2, 0]) cube([hdr_x1 - hdr_x0 + 2, 10, hdr_z1 + 0.6]);   // ヘッダー本体の逃げ
    }
}

module pcb_dummy() {
    color("green", 0.6) cube([pcb_w, pcb_h, pcb_t]);
    for (x = enc_x) color("silver") translate([x, enc_y, pcb_t]) cylinder(d = 6, h = 20);
    for (x = enc_x) color("orange") {
        translate([x - enc_body / 2, enc_y - enc_body / 2, pcb_t]) cube([enc_body, enc_body, enc_body_h]);
        translate([x, enc_y, pcb_t]) cylinder(d = 7, h = enc_body_h + 5);
    }
    for (x = jack_x) color("black")
        translate([x - jack_w / 2, pcb_h + 1.4 - jack_len, -jack_h]) cube([jack_w, jack_len, jack_h]);
}

// 下辺（y<0）は開けておく: 基板の下辺とシェルの下端が、CardputerZero本体の上面にそのまま載る。
// 基板の耳（ネジ止め用）は下に突き出して、本体の溝に入る
module keep() { translate([-50, 0, -50]) cube([200, 200, 100]); }
module ears() {
    for (x = ear_x) color("green", 0.6) difference() {
        union() {
            translate([x - ear_w / 2, -3.7, 0]) cube([ear_w, 3.7, pcb_t]);
            translate([x, -3.7, 0]) cylinder(d = ear_w, h = pcb_t);
        }
        translate([x, -3.7, -1]) cylinder(d = 2.1, h = 5);
    }
}

if (part == "base") intersection() { base(); keep(); }
else if (part == "top") rotate([180, 0, 0]) intersection() { top(); keep(); }   // 天板を下にして印刷
else {
    color("gray") intersection() { base(); keep(); }
    pcb_dummy();
    ears();
    color("white", 0.5) translate([0, 0, 0.02]) intersection() { top(); keep(); }
}
