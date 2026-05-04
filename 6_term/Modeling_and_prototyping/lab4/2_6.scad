$fn = 96;

eps = 0.01;
cut_eps = 2;

body_x = 40;
body_y = 35;
body_z = 65;

hole_rect_x = 26;
hole_rect_y = 26;

hole_rect_shift_x = 0;
hole_rect_shift_y = 0;
hole_rect_bbox = 26;
hole_rect_side = hole_rect_bbox / sqrt(2);

rib_width_x  = 7;
rib_depth_y  = 10;
rib_height_z = 45;
rib_shift_x  = 0;

boss_d = 30;
boss_len = 5;
boss_center_y = 0;
boss_center_z = 20;

cross_hole_d = 18;
cross_hole_y = boss_center_y;
cross_hole_z = boss_center_z;

lower_x = 50;
lower_y = 80;
lower_z = 35;

upper_shift_x = 0;
upper_shift_y = 0;

lower_chamfer_y = 5;
lower_chamfer_z = 5;

bottom_slot_y = 50;
bottom_slot_z = 10;
bottom_slot_shift_y = 0;


side_notch_x = 20;
side_notch_depth_y = 10;
side_notch_z = lower_z + 1;
side_notch_bottom_z = -0.5;
side_notch_shift_x = 0;


module main_body() {
    translate([-body_x/2, -body_y/2, 0])
        cube([body_x, body_y, body_z]);
}


module vertical_rect_hole() {
    translate([
        upper_shift_x + hole_rect_shift_x,
        upper_shift_y + hole_rect_shift_y,
        -cut_eps
    ])
        linear_extrude(
            height = lower_z + body_z + 2*cut_eps,
            convexity = 10
        )
            rotate(45)
                square([hole_rect_side, hole_rect_side], center = true);
}


module rib_y(side = 1) {
    hull() {
        translate([
            rib_shift_x - rib_width_x/2,
            (side > 0) ? body_y/2 : -body_y/2 - rib_depth_y,
            0
        ])
            cube([rib_width_x, rib_depth_y, eps]);

        translate([
            rib_shift_x - rib_width_x/2,
            (side > 0) ? body_y/2 - eps : -body_y/2,
            rib_height_z - eps
        ])
            cube([rib_width_x, eps, eps]);
    }
}


module side_boss(side = 1) {
    translate([
        side * (body_x/2 + boss_len/2),
        boss_center_y,
        boss_center_z
    ])
        rotate([0, 90, 0])
            cylinder(h = boss_len, d = boss_d, center = true);
}


module horizontal_cross_hole() {
    total_len = body_x + 2*boss_len + 2*eps;

    translate([0, cross_hole_y, cross_hole_z])
        rotate([0, 90, 0])
            cylinder(h = total_len, d = cross_hole_d, center = true);
}


module upper_part() {
    difference() {
        union() {
            main_body();

            rib_y( 1);
            rib_y(-1);

            side_boss( 1);
            side_boss(-1);
        }

        horizontal_cross_hole();
    }
}


module lower_body() {
    translate([-lower_x/2, -lower_y/2, 0])
        cube([lower_x, lower_y, lower_z]);
}


module prism_along_x(points_yz, x_len) {
    multmatrix([
        [0, 0, 1, 0],
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1]
    ])
        linear_extrude(height = x_len, center = true, convexity = 10)
            polygon(points = points_yz);
}

module top_chamfer_along_x(side = 1) {

    y_inner = side * (lower_y/2 - lower_chamfer_y);
    y_edge  = side * (lower_y/2);
    y_outer = side * (lower_y/2 + cut_eps);

    z_top   = lower_z;
    z_edge  = lower_z - lower_chamfer_z;

    pts = [
        [y_inner, z_top],
        [y_outer, z_top + cut_eps],
        [y_outer, z_edge - cut_eps],
        [y_edge,  z_edge]
    ];

    prism_along_x(pts, lower_x + 2*cut_eps);
}

module bottom_slot_along_x() {
    translate([
        -(lower_x + 2*eps)/2,
        bottom_slot_shift_y - bottom_slot_y/2,
        -eps
    ])
        cube([
            lower_x + 2*eps,
            bottom_slot_y,
            bottom_slot_z + eps
        ]);
}


module side_notch_from_y(side = 1) {
    y0 = (side > 0)
        ? lower_y/2 - side_notch_depth_y
        : -lower_y/2 - eps;

    translate([
        side_notch_shift_x - side_notch_x/2,
        y0,
        side_notch_bottom_z
    ])
        cube([
            side_notch_x,
            side_notch_depth_y + eps,
            side_notch_z
        ]);
}


module lower_part() {
    difference() {
        lower_body();

        top_chamfer_along_x( 1);
        top_chamfer_along_x(-1);

        bottom_slot_along_x();

        side_notch_from_y( 1);
        side_notch_from_y(-1);
    }
}


difference() {
    union() {
        lower_part();

        translate([upper_shift_x, upper_shift_y, lower_z])
            upper_part();
    }

    vertical_rect_hole();
}