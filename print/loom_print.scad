// 3D-printed parts for the rigid heddle loom.
// Open in OpenSCAD, choose 'part' in the Customizer, F6 (render) and export as STL.
// Print settings: PETG or PLA, 0.2 mm layers, 4 walls, 40 % infill.
// You can also make print-ready STLs without OpenSCAD with generate_stl.py (same dimensions).

/* [Choice] */
part = "all"; // [all, ratchet_front, ratchet_back, pawl, knob, collar, filing_jig]

/* [Dimensions] */
dowel_d       = 21.7;  // diameter of the roller dowel (measured; nominal 22 mm)
clearance     = 0.4;   // extra bore for print tolerance
flat_distance = 18.5;  // distance between the two filed flats on the shaft
flat_length   = 60.0;  // length of the flats from the end of the shaft
screw_hole    = 3.8;   // locking hole for a 3.5 x 25 wood screw
teeth         = 16;
r_tip         = 35;    // outer radius of the ratchet wheel
r_root        = 29;    // root radius of the teeth
wheel_t       = 10;    // thickness of ratchet wheel = thickness of pawl
hub_d         = 42;
hub_l         = 14;
pawl_length   = 41;    // distance from pivot to pawl tip
pawl_hole     = 5.4;   // M5 pivot bolt
knob_d        = 90;
knob_t        = 18;
jig_d         = 36;    // outer diameter of the filing jig

$fn = 96;
bore = dowel_d + clearance;

module hub(l) {
    // hub with one radial locking hole in the +x direction (centred on a flat of the double-D bore)
    difference() {
        cylinder(d = hub_d, h = l);
        translate([0, 0, l / 2]) rotate([0, 90, 0]) cylinder(d = screw_hole, h = hub_d, $fn = 24);
    }
}

module double_d(h) {
    // bore for the filed shaft: round, with two flats perpendicular to x
    intersection() {
        cylinder(d = bore, h = h);
        translate([-(flat_distance + clearance) / 2, -bore, 0]) cube([flat_distance + clearance, 2 * bore, h]);
    }
}

module ratchet() {
    step = 360 / teeth;
    difference() {
        union() {
            linear_extrude(wheel_t) polygon([
                for (i = [0 : teeth - 1]) each [
                    [r_root * cos(i * step), r_root * sin(i * step)],
                    [r_tip * cos((i + 0.92) * step), r_tip * sin((i + 0.92) * step)]
                ]
            ]);
            translate([0, 0, wheel_t - 0.01]) hub(hub_l);
        }
        translate([0, 0, -1]) double_d(wheel_t + hub_l + 2);
    }
}

module pawl() {
    // pivot at the origin, tip at (-pawl_length, 0), release tab to the right
    difference() {
        linear_extrude(wheel_t) union() {
            hull() {
                circle(d = 16);
                translate([-pawl_length + 6, 0]) circle(d = 10);
            }
            // tip: the straight face catches behind the radial tooth flank
            polygon([[-pawl_length + 6, -5], [-pawl_length, -1], [-pawl_length, 1.5], [-pawl_length + 6, 5]]);
            hull() {
                circle(d = 12);
                translate([22, 6]) circle(d = 10);
            }
        }
        translate([0, 0, -1]) cylinder(d = pawl_hole, h = wheel_t + 2);
    }
}

module knob() {
    lobes = 5;
    difference() {
        union() {
            linear_extrude(knob_t) offset(r = 6) offset(delta = -6) union() {
                circle(d = knob_d * 0.55);
                for (i = [0 : lobes - 1]) rotate(i * 360 / lobes)
                    translate([knob_d / 2 - 12, 0]) circle(d = 24);
                for (i = [0 : lobes - 1]) rotate(i * 360 / lobes)
                    hull() { circle(d = 18); translate([knob_d / 2 - 12, 0]) circle(d = 18); }
            }
            translate([0, 0, knob_t - 0.01]) hub(hub_l);
        }
        translate([0, 0, -1]) double_d(knob_t + hub_l + 2);
    }
}

module collar() {
    difference() {
        hub(hub_l);
        translate([0, 0, -1]) cylinder(d = bore, h = hub_l + 2);
    }
}

module filing_jig() {
    // sleeve over the shaft with a stop at the bottom; file until the shaft is level with the window edges
    base = 3;
    difference() {
        cylinder(d = jig_d, h = base + flat_length + 15);
        translate([0, 0, base]) cylinder(d = bore, h = flat_length + 16);
        translate([0, 0, -1]) cylinder(d = 6, h = base + 2);
        for (s = [-1, 1]) translate([s > 0 ? flat_distance / 2 : -flat_distance / 2 - jig_d / 2, -jig_d, base])
            cube([jig_d / 2, 2 * jig_d, flat_length]);
    }
}

// front (cloth roller) and back (warp roller) are mirror images: the rollers pull back in opposite directions
if (part == "ratchet_back") ratchet();
else if (part == "ratchet_front") mirror([0, 1, 0]) ratchet();
else if (part == "pawl") pawl();
else if (part == "knob") knob();
else if (part == "collar") collar();
else if (part == "filing_jig") filing_jig();
else {
    // print plate with all parts for one loom (2 rollers)
    translate([0, 0, 0]) mirror([0, 1, 0]) ratchet();   // front
    translate([80, 0, 0]) ratchet();                     // back
    for (i = [0, 1]) translate([i * 100 + 10, 95, 0]) knob();
    for (i = [0, 1]) translate([i * 75 + 210, 0, 0]) pawl();
    for (i = [0, 1]) translate([i * 50 + 210, 40, 0]) collar();
    translate([230, 100, 0]) filing_jig();
}
